# -*- coding: utf-8 -*-
#
# Copyright © 2008-2015  Red Hat, Inc. All rights reserved.
# Copyright © 2008-2015  Luke Macken <lmacken@redhat.com>
# Copyright © 2008  Kushal Das <kushal@fedoraproject.org>
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.  You should have
# received a copy of the GNU General Public License along with this program; if
# not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth
# Floor, Boston, MA 02110-1301, USA. Any Red Hat trademarks that are
# incorporated in the source code or documentation are not subject to the GNU
# General Public License and may only be used or replicated with the express
# permission of Red Hat, Inc.
#
# Author(s): Luke Macken <lmacken@redhat.com>
#            Kushal Das <kushal@fedoraproject.org>
#            Martin Bříza <mbriza@redhat.com>

"""
A cross-platform graphical interface for the LiveUSBCreator
"""

import os
import sys
import logging
import urlparse

from time import sleep
from datetime import datetime
from PyQt5.QtCore import pyqtProperty, pyqtSlot, QObject, QUrl, QDateTime, pyqtSignal, QThread, QAbstractListModel, QSortFilterProxyModel, QModelIndex, Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQml import qmlRegisterType, qmlRegisterUncreatableType, QQmlComponent, QQmlApplicationEngine, QQmlListProperty
from PyQt5.QtQuick import QQuickView

from liveusb import LiveUSBCreator, LiveUSBError, _
from liveusb.releases import releases, get_fedora_releases

if sys.platform == 'win32':
    from liveusb.urlgrabber.grabber import URLGrabber, URLGrabError
    from liveusb.urlgrabber.progress import BaseMeter
else:
    from urlgrabber.grabber import URLGrabber, URLGrabError
    from urlgrabber.progress import BaseMeter

try:
    import dbus.mainloop.pyqt5
    dbus.mainloop.pyqt5.DBusQtMainLoop(set_as_default=True)
except Exception, e:
    print(e)
    pass

MAX_FAT16 = 2047
MAX_FAT32 = 3999
MAX_EXT = 2097152

class ReleaseDownloadThread(QThread):
    downloadFinished = pyqtSignal(str)
    downloadError = pyqtSignal(str)

    def __init__(self, url, progress, proxies):
        QThread.__init__(self)
        self.url = url
        self.progress = progress
        self.proxies = proxies

    def run(self):
        self.grabber = URLGrabber(progress_obj=self.progress, proxies=self.proxies)
        home = os.getenv('HOME', 'USERPROFILE')
        filename = os.path.basename(urlparse.urlparse(self.url).path)
        try:
            iso = self.grabber.urlgrab(self.url, reget='simple')
        except URLGrabError, e:
            # TODO find out if this errno is _really_ benign
            if e.errno == 9: # Requested byte range not satisfiable.
                self.downloadFinished.emit(filename)
            else:
                self.downloadError.emit(e.strerror)
        else:
            self.downloadFinished.emit(iso)

class ReleaseDownload(QObject, BaseMeter):
    runningChanged = pyqtSignal()
    currentChanged = pyqtSignal()
    maximumChanged = pyqtSignal()
    pathChanged = pyqtSignal()

    _running = False
    _current = -1.0
    _maximum = -1.0
    _path = ''

    def __init__(self, parent):
        QObject.__init__(self, parent)
        self._grabber = ReleaseDownloadThread(parent.url, self, parent.live.get_proxies())

    def reset(self):
        self._running = False
        self._current = -1.0
        self._maximum = -1.0
        self.path = ''
        self.runningChanged.emit()
        self.currentChanged.emit()
        self.maximumChanged.emit()

    def start(self, filename=None, url=None, basename=None, size=None, now=None, text=None):
        self._maximum = size
        self._running = True
        self.maximumChanged.emit()
        self.runningChanged.emit()

    def update(self, amount_read, now=None):
        """ Update our download progressbar.

        :read: the number of bytes read so far
        """
        if self._current < amount_read:
            self._current = amount_read
            self.currentChanged.emit()

    def end(self, amount_read):
        self._current = amount_read
        self.currentChanged.emit()

    @pyqtSlot(str)
    def childFinished(self, iso):
        self.reset()
        self.path = iso
        self._running = False
        self.runningChanged.emit()

    @pyqtSlot(str)
    def childError(self, err):
        self.reset()

    @pyqtSlot(str)
    def run(self):
        if len(self.parent().path) <= 0:
            self._grabber.start()
            self._grabber.downloadFinished.connect(self.childFinished)
            self._grabber.downloadError.connect(self.childError)

    @pyqtSlot()
    def cancel(self):
        self._grabber.terminate()
        self.reset()

    @pyqtProperty(float, notify=maximumChanged)
    def maxProgress(self):
        return self._maximum

    @pyqtProperty(float, notify=currentChanged)
    def progress(self):
        return self._current

    @pyqtProperty(bool, notify=runningChanged)
    def running(self):
        return self._running

    @pyqtProperty(str, notify=pathChanged)
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if self._path != value:
            self._path = value
            self.parent().live.set_iso(value)
            self.pathChanged.emit()

class ReleaseWriterProgressThread(QThread):
    alive = True
    get_free_bytes = None
    drive = None
    totalSize = 0
    orig_free = 0

    def set_data(self, size, drive, freebytes):
        self.totalSize = size / 1024
        self.drive = drive
        self.get_free_bytes = freebytes
        self.orig_free = self.get_free_bytes()
        self.parent().maxProgress = self.totalSize

    def run(self):
        while self.alive:
            free = self.get_free_bytes()
            value = (self.orig_free - free) / 1024
            self.parent().progress = value
            if (value >= self.totalSize):
                break
            sleep(3)

    def stop(self):
        self.alive = False

    def terminate(self):
        self.parent().progress = self.totalSize
        self.terminate()


class ReleaseWriterThread(QThread):


    def __init__(self, parent, progressThread, useDD = False):
        QThread.__init__(self, parent)

        self.live = parent.live
        self.parent = parent
        self.progressThread = progressThread
        self._useDD = useDD


    def run(self):
        #handler = LiveUSBLogHandler(self.parent.status)
        #self.live.log.addHandler(handler)
        now = datetime.now()
        try:
            if self._useDD:
                self.ddImage(now)
            else:
                self.copyImage(now)
        except Exception, e:
            self.parent.status = e.args[0]
            self.live.log.exception(e)

        self.parent.running = False
        #self.live.log.removeHandler(handler)

    def ddImage(self, now):
        self.status = _("WARNING: You are about to perform a destructive install. This will destroy all data and partitions on your USB drive. Press 'Create Live USB' again to continue.")
        self.live.dd_image()
        #self.live.log.removeHandler(handler)
        duration = str(datetime.now() - now).split('.')[0]
        self.progressThread.stop()
        return

    def copyImage(self, now):

        self.parent.status = _("Checking the source image")
        self.live.check_free_space()

        if not self.live.opts.noverify:
            # Verify the MD5 checksum inside of the ISO image
            if not self.live.verify_iso_md5():
                #self.live.log.removeHandler(handler)
                return

            # If we know about this ISO, and it's SHA1 -- verify it
            release = self.live.get_release_from_iso()
            if release and ('sha1' in release or 'sha256' in release):
                if not self.live.verify_iso_sha1(self):
                    #self.live.log.removeHandler(handler)
                    return

        self.parent.status = _("Unpacking the image")
        # Setup the progress bar
        self.progressThread.set_data(size=self.live.totalsize,
                                     drive=self.live.drive['device'],
                                     freebytes=self.live.get_free_bytes)
        self.progressThread.start()

        self.live.extract_iso()

        self.parent.status = _("Writing the data")
        self.live.create_persistent_overlay()
        self.live.update_configs()
        self.live.install_bootloader()
        self.live.bootable_partition()

        self.parent.status = _("Checking the written data")
        if self.live.opts.device_checksum:
            self.live.calculate_device_checksum(progressThread=self)
        if self.live.opts.liveos_checksum:
            self.live.calculate_liveos_checksum()

        self.progressThread.stop()

        # Flush all filesystem buffers and unmount
        self.parent.status = "Flushing buffers"
        self.live.flush_buffers()
        self.parent.status = "Unmounting"
        self.live.unmount_device()
        self.parent.status = "Finished!"
        self.parent.finished = True

        duration = str(datetime.now() - now).split('.')[0]
        #self.parent.status = "Complete! (%s)" % duration

        self.progressThread.stop()

    def set_max_progress(self, maximum):
        self.parent.maxProgress = maximum

    def update_progress(self, value):
        self.parent.progress = value

class ReleaseWriter(QObject):
    runningChanged = pyqtSignal()
    currentChanged = pyqtSignal()
    maximumChanged = pyqtSignal()
    statusChanged = pyqtSignal()
    finishedChanged = pyqtSignal()

    _running = False
    _current = -1.0
    _maximum = -1.0
    _status = ""
    _finished = False

    def __init__(self, parent):
        QObject.__init__(self, parent)
        self.live = parent.live
        self.progressWatcher = ReleaseWriterProgressThread(self)
        self.worker = ReleaseWriterThread(self, self.progressWatcher, False)

    def reset(self):
        self._running = False
        self._current = -1.0
        self._maximum = -1.0
        self.runningChanged.emit()
        self.currentChanged.emit()
        self.maximumChanged.emit()

    @pyqtSlot()
    def run(self, useDD = False):
        self._running = True
        self._current = 0.0
        self._maximum = 100.0
        self.runningChanged.emit()
        self.currentChanged.emit()
        self.maximumChanged.emit()
        self.status = "Writing"
        self.worker.start()

    @pyqtSlot()
    def cancel(self):
        self.progressWatcher.stop()
        self.worker.terminate()
        self.reset()

    @pyqtProperty(bool, notify=runningChanged)
    def running(self):
        return self._running

    @running.setter
    def running(self, value):
        if self._running != value:
            self._running = value
            self.runningChanged.emit()

    @pyqtProperty(float, notify=maximumChanged)
    def maxProgress(self):
        return self._maximum

    @maxProgress.setter
    def maxProgress(self, value):
        if (value != self._maximum):
            self._maximum = value
            self.maximumChanged.emit()

    @pyqtProperty(float, notify=currentChanged)
    def progress(self):
        return self._current

    @progress.setter
    def progress(self, value):
        if (value != self._current):
            self._current = value
            self.currentChanged.emit()

    @pyqtProperty(str, notify=statusChanged)
    def status(self):
        return self._status

    @status.setter
    def status(self, s):
        if self._status != s:
            self._status = s
            self.statusChanged.emit()

    @pyqtProperty(bool, notify=finishedChanged)
    def finished(self):
        return self._finished

    @finished.setter
    def finished(self, value):
        if self._finished != value:
            self._finished = value
            self.finishedChanged.emit()


class Release(QObject):
    screenshotsChanged = pyqtSignal()
    infoChanged = pyqtSignal()
    statusChanged = pyqtSignal()
    pathChanged = pyqtSignal()
    sizeChanged = pyqtSignal()

    def __init__(self, parent, index, live=None, name = '', logo = '', size = 0, arch = '', fullName = '', releaseDate = QDateTime(), shortDescription = '', fullDescription = '', isLocal = False, screenshots = [], url=''):
        QObject.__init__(self, parent)

        self._index = index
        self.live = live
        self._name = name.replace('_', ' ')
        self._logo = logo
        self._size = size
        self._arch = arch
        self._fullName = fullName
        self._releaseDate = releaseDate
        self._shortDescription = shortDescription
        self._fullDescription = fullDescription
        self._isLocal = isLocal
        self._screenshots = screenshots
        self._url = url
        self._path = ''
        self._info = ''

        if self._logo == '':
            if self._name == 'Fedora Workstation':
                self._logo = '../../data/logo-color-workstation.png'
            elif self._name == 'Fedora Server':
                self._logo = '../../data/logo-color-server.png'
            elif self._name == 'Fedora Cloud':
                self._logo = '../../data/logo-color-cloud.png'
            elif self._name == 'Fedora KDE':
                self._logo = '../../data/logo-plasma5.png'
            elif self._name == 'Fedora Xfce':
                self._logo = '../../data/logo-xfce.svg'
            elif self._name == 'Fedora LXDE':
                self._logo = '../../data/logo-lxde.png'
            else:
                self._logo = '../../data/logo-fedora.svg'

        if self._name == "Fedora Workstation":
            self._fullDescription = "Fedora Workstation is a reliable, user-friendly, and powerful operating system for your laptop or desktop computer. It supports a wide range of developers, from hobbyists and students to professionals in corporate environments."
        if self._name == "Fedora Server":
            self._fullDescription = "Fedora Server is a powerful, flexible operating system that includes the best and latest datacenter technologies. It puts you in control of all your infrastructure and services."
        if self._name == "Fedora Cloud":
            self._fullDescription = "Fedora Cloud provides a minimal image of Fedora for use in public and private cloud environments. It includes just the bare essentials, so you get enough to run your cloud application -- and nothing more."

        self._download = ReleaseDownload(self)
        self._download.pathChanged.connect(self.pathChanged)

        self._writer = ReleaseWriter(self)

        self._download.runningChanged.connect(self.inspectDestination)

        self.pathChanged.connect(self.statusChanged)
        self._download.runningChanged.connect(self.statusChanged)
        self._writer.runningChanged.connect(self.statusChanged)
        self._writer.statusChanged.connect(self.statusChanged)


    @pyqtSlot()
    def get(self):
        if len(self._path) <= 0:
            self._download.run()

    @pyqtSlot()
    def write(self):
        self._writer.run()

    @pyqtSlot()
    def inspectDestination(self):
        if self.live.blank_mbr():
            self.info = _("The Master Boot Record on your device is blank. Writing the image will reset the MBR on this device")
        elif not self.live.mbr_matches_syslinux_bin():
            self.info = _("The Master Boot Record on your device does not match your system's syslinux MBR.\n"
                          "If you have trouble booting it, try setting the \"Reset the MBR\" advanced option.")

        try:
            self.live.mount_device()
        except LiveUSBError, e:
            self.info = e.args[0]
            self._running = False
            self.runningChanged.emit()
        except OSError, e:
            self.info = _('Unable to mount device')
            self._running = False
            self.runningChanged.emit()

        if self.live.existing_liveos():
            self.info += _("\nYour device already contains a LiveOS. If you continue, it will be overwritten.")
            #TODO

        self.live.verify_filesystem()
        if not self.live.drive['uuid'] and not self.live.label:
            self.parent.status = _("Error: Cannot set the label or obtain "
                          "the UUID of your device.  Unable to continue.")
            #self.live.log.removeHandler(handler)
            return

    @pyqtProperty(int, constant=True)
    def index(self):
        return self._index

    @pyqtProperty(str, constant=True)
    def name(self):
        return self._name

    @pyqtProperty(str, constant=True)
    def logo(self):
        return self._logo

    @pyqtProperty(float, notify=sizeChanged)
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        if value != self._size:
            self._size = value
            self.sizeChanged.emit()

    @pyqtProperty(str, constant=True)
    def arch(self):
        return self._arch

    @pyqtProperty(str, constant=True)
    def fullName(self):
        return self._fullName

    @pyqtProperty(QDateTime, constant=True)
    def releaseDate(self):
        return self._releaseDate

    @pyqtProperty(str, constant=True)
    def shortDescription(self):
        return self._shortDescription

    @pyqtProperty(str, constant=True)
    def fullDescription(self):
        return self._fullDescription

    @pyqtProperty(bool, constant=True)
    def isLocal(self):
        return self._isLocal

    @pyqtProperty(QQmlListProperty, notify=screenshotsChanged)
    def screenshots(self):
        return QQmlListProperty(str, self, self._screenshots)

    @pyqtProperty(str, constant=True)
    def url(self):
        return self._url

    @pyqtProperty(str, notify=pathChanged)
    def path(self):
        return self._download.path

    @path.setter
    def path(self, value):
        if value.startswith('file://'):
            value = value.replace('file://', '', 1)
        if self._path != value:
            self._download.path = value
            self.pathChanged.emit();
            self.size = self.live.isosize

    @pyqtProperty(bool, notify=pathChanged)
    def readyToWrite(self):
        return len(self.path) != 0

    @pyqtProperty(ReleaseDownload, constant=True)
    def download(self):
        return self._download

    @pyqtProperty(ReleaseWriter, constant=True)
    def writer(self):
        return self._writer

    @pyqtProperty(str, notify=statusChanged)
    def status(self):
        if not self._download.running and not self.readyToWrite and not self._writer.running:
            return 'Starting'
        elif self._download.running:
            return 'Downloading'
        elif self.readyToWrite and not self._writer.running and not self._writer.finished:
            return 'Ready to write'
        elif self._writer.status:
            return self._writer.status
        else:
            return 'Finished'

    @pyqtProperty(str, notify=infoChanged)
    def info(self):
        return self._info

    @info.setter
    def info(self, value):
        if self._info != value:
            self._info = value
            self.infoChanged.emit()

class ReleaseListModel(QAbstractListModel):
    def __init__(self, parent, title=False):
        QAbstractListModel.__init__(self, parent)
        self._title = title

    def rowCount(self, parent=QModelIndex()):
        if self._title:
            return min(6, len(self.parent().releaseData))
        else:
            return len(self.parent().releaseData)

    def roleNames(self):
        return {Qt.UserRole + 1 : "release"}

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            return self.parent().releaseData[index.row()]
        return None

class ReleaseListProxy(QSortFilterProxyModel):
    archChanged = pyqtSignal()
    nameFilterChanged = pyqtSignal()

    _archFilter = ['x86_64']
    _nameFilter = ''

    _archMap = {'64bit': ['x86_64'], '32bit': ['i686','i386']}


    def __init__(self, parent, sourceModel):
        QSortFilterProxyModel.__init__(self, parent)
        self.setSourceModel(sourceModel)

    def filterAcceptsRow(self, sourceRow, sourceParent):
        row = self.sourceModel().index(sourceRow, 0, sourceParent).data()
        if len(self._archFilter) == 0 or row.arch.lower() in [x.lower() for x in self._archFilter] or row.isLocal:
            if len(self._nameFilter) == 0 or self._nameFilter.lower() in row.name.lower():
                return True
        return False

    @pyqtProperty(str, notify=nameFilterChanged)
    def nameFilter(self):
        return self._nameFilter

    @nameFilter.setter
    def nameFilter(self, value):
        if value != self._nameFilter:
            self._nameFilter = value
            self.nameFilterChanged.emit()
            self.invalidateFilter()

    @pyqtProperty('QStringList', constant=True)
    def possibleArchs(self):
        return self._archMap.keys()

    @pyqtProperty(str, notify=archChanged)
    def archFilter(self):
        for name, abbrs in self._archMap.items():
            if abbrs == self._archFilter:
                return name
        self.archFilter = '64bit'
        return '64bit'

    @archFilter.setter
    def archFilter(self, value):
        if self._archMap.has_key(value) and self.archFilter != self._archMap[value]:
            self._archFilter = self._archMap[value]
            self.archChanged.emit()
            self.invalidateFilter()

class LiveUSBLogHandler(logging.Handler):

    def __init__(self, cb):
        logging.Handler.__init__(self)
        self.cb = cb

    def emit(self, record):
        if record.levelname in ('INFO', 'ERROR', 'WARN'):
            self.cb(record.msg)

class USBDrive(QObject):

    def __init__(self, parent, name, drive):
        QObject.__init__(self, parent)
        self._name = name
        self._drive = drive

    @pyqtProperty(str, constant=True)
    def text(self):
        return self._name

    @pyqtProperty(str, constant=True)
    def drive(self):
        return self._drive

class LiveUSBData(QObject):
    releasesChanged = pyqtSignal()
    currentImageChanged = pyqtSignal()
    usbDrivesChanged = pyqtSignal()
    currentDriveChanged = pyqtSignal()

    _currentIndex = 0
    _currentDrive = 0

    _options = [_("Use <b>dd</b> to write the image - this will erase everything on your portable drive"), _("Reset the MBR (Master Boot Record)")]
    _optionValues = [False, False]

    def __init__(self, opts):
        QObject.__init__(self)
        self.live = LiveUSBCreator(opts=opts)
        self._releaseModel = ReleaseListModel(self)
        self._releaseProxy = ReleaseListProxy(self, self._releaseModel)
        self._titleReleaseModel = ReleaseListModel(self, True)
        self._titleReleaseProxy = ReleaseListProxy(self, self._titleReleaseModel)
        self.releaseData = [Release(self, 0, self.live, name='Custom OS...', shortDescription='<pick from file chooser>', fullDescription='Here you can choose a OS image from your hard drive to be written to your flash disk', isLocal=True, logo='../../data/icon-folder.svg')]
        for release in releases:
            self.releaseData.append(Release(self,
                                            len(self.releaseData),
                                            self.live,
                                            name='Fedora '+release['variant'],
                                            shortDescription='Fedora'+(' Minimal ' if release['netinst'] and not release['variant'] == 'Cloud' else ' ')+release['variant']+' '+release['version']+(' 64bit' if release['arch']=='x86_64' else ' 32bit'),
                                            arch=release['arch'],
                                            size=release['size'],
                                            url=release['url']
                                    ))
        self._usbDrives = []

        try:
            self.live.detect_removable_drives(callback=self.USBDeviceCallback)
        except LiveUSBError, e:
            pass # TODO

    def USBDeviceCallback(self):
        tmpDrives = []
        previouslySelected = ""
        if len(self._usbDrives) > 0:
            previouslySelected = self._usbDrives[self._currentDrive].drive['device']
        for drive, info in self.live.drives.items():
            name = ''
            if info['vendor'] and info['model']:
                name = info['vendor'] + ' ' + info['model']
            elif info['label']:
                name = info['label']
            else:
                name = info['device']

            gb = 1000.0 # if it's decided to use base 2 values, change this

            if info['fullSize']:
                pass
                if info['fullSize'] < gb:
                    name += ' (%.1f B)'  % (info['fullSize'] / (gb ** 0))
                elif info['fullSize'] < gb * gb:
                    name += ' (%.1f KB)' % (info['fullSize'] / (gb ** 1))
                elif info['fullSize'] < gb * gb * gb:
                    name += ' (%.1f MB)' % (info['fullSize'] / (gb ** 2))
                elif info['fullSize'] < gb * gb * gb * gb:
                    name += ' (%.1f GB)' % (info['fullSize'] / (gb ** 3))
                else:
                    name += ' (%.1f TB)' % (info['fullSize'] / (gb ** 4))

            tmpDrives.append(USBDrive(self, name, info))

        if tmpDrives != self._usbDrives:
            self._usbDrives = tmpDrives
            self.usbDrivesChanged.emit()

            self.currentDrive = 0
            for i, drive in enumerate(self._usbDrives):
                if drive.drive['device'] == previouslySelected:
                    self.currentDrive = i

    @pyqtProperty(ReleaseListModel, notify=releasesChanged)
    def releaseModel(self):
        return self._releaseModel

    @pyqtProperty(ReleaseListProxy, notify=releasesChanged)
    def releaseProxyModel(self):
        return self._releaseProxy

    @pyqtProperty(ReleaseListModel, notify=releasesChanged)
    def titleReleaseModel(self):
        return self._titleReleaseProxy

    @pyqtProperty(int, notify=currentImageChanged)
    def currentIndex(self):
        return self._currentIndex

    @currentIndex.setter
    def currentIndex(self, value):
        if value != self._currentIndex:
            self._currentIndex = value
            self.currentImageChanged.emit()

    @pyqtProperty(Release, notify=currentImageChanged)
    def currentImage(self):
        return self.releaseData[self._currentIndex]

    @pyqtProperty(QQmlListProperty, notify=usbDrivesChanged)
    def usbDrives(self):
        return QQmlListProperty(USBDrive, self, self._usbDrives)

    @pyqtProperty('QStringList', notify=usbDrivesChanged)
    def usbDriveNames(self):
        return list(i.text for i in self._usbDrives)

    @pyqtProperty(int, notify=currentDriveChanged)
    def currentDrive(self):
        return self._currentDrive

    @currentDrive.setter
    def currentDrive(self, value):
        if len(self._usbDrives) == 0:
            self._currentDrive
            return
        if value > len(self._usbDrives):
            value = 0
            self.currentDriveChanged.emit()
        if len(self._usbDrives) != 0 and (self._currentDrive != value or self.live.drive != self._usbDrives[value].drive['device']):
            self._currentDrive = value
            if len(self._usbDrives) > 0:
                self.live.drive = self._usbDrives[self._currentDrive].drive['device']
            self.currentDriveChanged.emit()
            for r in self.releaseData:
                r.download.finished = False

    @pyqtProperty('QStringList', constant=True)
    def options(self):
        return self._options

    @pyqtSlot(int, bool)
    def setOption(self, index, value):
        self._options[index] = value


class LiveUSBApp(QApplication):
    """ Main application class """
    def __init__(self, opts, args):
        QApplication.__init__(self, args)
        qmlRegisterUncreatableType(ReleaseDownload, "LiveUSB", 1, 0, "Download", "Not creatable directly, use the liveUSBData instance instead")
        qmlRegisterUncreatableType(ReleaseWriter, "LiveUSB", 1, 0, "Writer", "Not creatable directly, use the liveUSBData instance instead")
        qmlRegisterUncreatableType(ReleaseListModel, "LiveUSB", 1, 0, "ReleaseModel", "Not creatable directly, use the liveUSBData instance instead")
        qmlRegisterUncreatableType(Release, "LiveUSB", 1, 0, "Release", "Not creatable directly, use the liveUSBData instance instead")
        qmlRegisterUncreatableType(USBDrive, "LiveUSB", 1, 0, "Drive", "Not creatable directly, use the liveUSBData instance instead")
        qmlRegisterUncreatableType(LiveUSBData, "LiveUSB", 1, 0, "Data", "Use the liveUSBData root instance")
        view = QQmlApplicationEngine()
        self.data = LiveUSBData(opts)
        view.rootContext().setContextProperty("liveUSBData", self.data);
        view.load(QUrl('liveusb/liveusb.qml'))
        view.rootObjects()[0].show()
        self.exec_()
