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

There was a move from the procedural code that was directly changing the UI itself.
Now, we expose a set of properties representing each object we're manipulating in the back-end.
The exposed properties are then handled independently in the UI.

For example, when the image is being written, we just change the "writing" property. The UI then locks itself up based
on this property. Basically, this means every relevant "enabled" property of the UI elements is bound to the "writing"
property of the backend.
"""

import os
import sys
import logging
import urlparse


from time import sleep
from datetime import datetime
from PyQt5.QtCore import pyqtProperty, pyqtSlot, QObject, QUrl, QDateTime, pyqtSignal, QThread, QAbstractListModel, QSortFilterProxyModel, QModelIndex, Qt, QTranslator, QLocale, QTimer
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import qmlRegisterType, qmlRegisterUncreatableType, QQmlComponent, QQmlApplicationEngine, QQmlListProperty, QQmlEngine
from PyQt5 import QtQuick

import resources_rc
import qml_rc

from liveusb import LiveUSBCreator, LiveUSBError, _
from liveusb.releases import releases

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
    pass

MAX_FAT16 = 2047
MAX_FAT32 = 3999
MAX_EXT = 2097152

class ReleaseDownloadThread(QThread):
    """ Heavy lifting in the process the iso file download """
    downloadFinished = pyqtSignal(str)
    downloadError = pyqtSignal(str)

    def __init__(self, progress, proxies):
        QThread.__init__(self)
        self.progress = progress
        self.proxies = proxies

    def run(self):
        self.grabber = URLGrabber(progress_obj=self.progress, proxies=self.proxies)
        home = os.getenv('HOME', 'USERPROFILE')
        filename = os.path.basename(urlparse.urlparse(self.progress.release.url).path)
        for folder in ('Downloads', 'My Documents'):
            if os.path.isdir(os.path.join(home, folder)):
                filename = os.path.join(home, folder, filename)
                break
        try:
            iso = self.grabber.urlgrab(self.progress.release.url, filename=filename, reget='simple')
            print iso
        except URLGrabError, e:
            # TODO find out if this errno is _really_ benign
            if e.errno == 9: # Requested byte range not satisfiable.
                self.downloadFinished.emit(filename)
            else:
                self.downloadError.emit(e.strerror)
        else:
            self.downloadFinished.emit(iso)

class ReleaseDownload(QObject, BaseMeter):
    """ Wrapper for the iso download process.
    It exports properties to track the percentage and the file with the result.
    """
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
        self.release = parent
        self._grabber = ReleaseDownloadThread(self, parent.live.get_proxies())
        self._live = parent.live

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
            self._grabber.downloadFinished.connect(self.childFinished)
            self._grabber.downloadError.connect(self.childError)
            self._grabber.start()

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
            self._live.set_iso(value)
            self.pathChanged.emit()

class ReleaseWriterProgressThread(QThread):
    """ Periodically checks how the write progresses """
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
    """ The actual write to the portable drive """

    def __init__(self, parent, progressThread):
        QThread.__init__(self, parent)

        self.live = parent.live
        self.parent = parent
        self.progressThread = progressThread


    def run(self):
        # TODO move this to the backend
        #handler = LiveUSBLogHandler(self.parent.status)
        #self.live.log.addHandler(handler)
        now = datetime.now()
        try:
            self.live.verify_filesystem()
            if not self.live.drive['uuid'] and not self.live.label:
                self.parent.release.addError(_('Error: Cannot set the label or obtain '
                              'the UUID of your device.  Unable to continue.'))
                self.parent.running = False
                return
            if self.parent.release.liveUSBData.option('dd'):
                self.ddImage(now)
            else:
                self.copyImage(now)
        except Exception, e:
            self.parent.release.addError(e.args[0])
            self.live.log.exception(e)

        self.parent.running = False
        #self.live.log.removeHandler(handler)

    def ddImage(self, now):
        # TODO move this to the backend
        self.live.dd_image()
        #self.live.log.removeHandler(handler)
        #duration = str(datetime.now() - now).split('.')[0]
        self.parent.status = 'Finished!'
        self.parent.finished = True
        self.progressThread.stop()
        return

    def copyImage(self, now):
        # TODO move this to the backend

        self.parent.status = _('Checking the source image')
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

        self.parent.status = _('Unpacking the image')
        # Setup the progress bar
        self.progressThread.set_data(size=self.live.totalsize,
                                     drive=self.live.drive['device'],
                                     freebytes=self.live.get_free_bytes)
        self.progressThread.start()

        self.live.extract_iso()

        if self.live.blank_mbr() or self.parent.release.liveUSBData.option('resetMBR'):
            self.live.reset_mbr()

        self.parent.status = _('Writing the data')
        self.live.create_persistent_overlay()
        self.live.update_configs()
        self.live.install_bootloader()
        self.live.bootable_partition()

        self.parent.status = _('Checking the written data')
        if self.live.opts.device_checksum:
            self.live.calculate_device_checksum(progressThread=self)
        if self.live.opts.liveos_checksum:
            self.live.calculate_liveos_checksum()

        self.progressThread.stop()

        # Flush all filesystem buffers and unmount
        self.live.flush_buffers()
        self.live.unmount_device()
        self.parent.status = _('Finished!')
        self.parent.finished = True

        duration = str(datetime.now() - now).split('.')[0]
        #self.parent.status = 'Complete! (%s)' % duration

        self.progressThread.stop()

    def set_max_progress(self, maximum):
        self.parent.maxProgress = maximum

    def update_progress(self, value):
        self.parent.progress = value

class ReleaseWriter(QObject):
    """ Here we can track the progress of the writing and control it """
    runningChanged = pyqtSignal()
    currentChanged = pyqtSignal()
    maximumChanged = pyqtSignal()
    statusChanged = pyqtSignal()
    finishedChanged = pyqtSignal()

    _running = False
    _current = -1.0
    _maximum = -1.0
    _status = ''
    _finished = False

    def __init__(self, parent):
        QObject.__init__(self, parent)
        self.live = parent.live
        self.release = parent
        self.progressWatcher = ReleaseWriterProgressThread(self)
        self.worker = ReleaseWriterThread(self, self.progressWatcher)

    def reset(self):
        self._running = False
        self._current = -1.0
        self._maximum = -1.0
        self.runningChanged.emit()
        self.currentChanged.emit()
        self.maximumChanged.emit()

    @pyqtSlot()
    def run(self):
        self._running = True
        self._current = 0.0
        self._maximum = 100.0
        self.runningChanged.emit()
        self.currentChanged.emit()
        self.maximumChanged.emit()
        self.status = 'Writing'
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
    ''' Contains the information about the particular release of Fedora
        I think there should be a cleanup of all the properties - there seem to be more of them than needed
    '''
    screenshotsChanged = pyqtSignal()
    errorChanged = pyqtSignal()
    warningChanged = pyqtSignal()
    infoChanged = pyqtSignal()
    statusChanged = pyqtSignal()
    pathChanged = pyqtSignal()
    sizeChanged = pyqtSignal()

    _path = ''

    _archMap = {'64bit': ['x86_64'], '32bit': ['i686','i386']} #, 'ARM': ['armv7hl']}

    def __init__(self, parent, index, live, data):
        QObject.__init__(self, parent)

        self._index = index
        self.live = live
        self.liveUSBData = parent

        self._size = 0

        self._data = data

        self._info = []
        self._warning = []
        self._error = []

        self._download = ReleaseDownload(self)
        self._download.pathChanged.connect(self.pathChanged)

        self._writer = ReleaseWriter(self)

        self._download.runningChanged.connect(self.inspectDestination)

        self.pathChanged.connect(self.statusChanged)
        self._download.runningChanged.connect(self.statusChanged)
        self._writer.runningChanged.connect(self.statusChanged)
        self._writer.statusChanged.connect(self.statusChanged)

        parent.releaseProxyModel.archChanged.connect(self.sizeChanged)
        parent.releaseProxyModel.archChanged.connect(self.pathChanged)


    @pyqtSlot()
    def get(self):
        if len(self._path) <= 0:
            self._download.run()

    @pyqtSlot()
    def write(self):
        self._warning = []
        self._error = []
        self.errorChanged.emit()
        self.warningChanged.emit()
        self._writer.run()

    @pyqtSlot()
    def inspectDestination(self):
        if self._writer.running:
            return
        self._warning = []
        self.warningChanged.emit()
        self._info = []
        self.infoChanged.emit()
        self._error = []
        self.errorChanged.emit()

        if not self.live.drive:
            return

        if self.parent().option('dd'):
            self.addWarning(_('You are about to perform a destructive install. This will erase all data and partitions on your USB drive'))
        else:
            if self.live.blank_mbr():
                self.addInfo(_('The Master Boot Record on your device is blank. Writing the image will reset the MBR on this device'))
            elif not self.live.mbr_matches_syslinux_bin() and not self.parent().option('resetMBR'):
                self.addInfo(_('The Master Boot Record on your device does not match your system\'s syslinux MBR.\n'
                              'If you have trouble booting it, try setting the \"Reset the MBR\" advanced option.'))

        try:
            self.live.mount_device()
        except LiveUSBError, e:
            self.addInfo(e.args[0])
        except OSError, e:
            self.addInfo(_('Unable to mount device'))

        if self.live.existing_liveos() and not self.parent().option('dd'):
            self.addWarning(_('Your device already contains a live OS. If you continue, it will be overwritten.'))

    @pyqtProperty(int, constant=True)
    def index(self):
        return self._index

    @pyqtProperty(bool, constant=True)
    def isSeparator(self):
        return self._data['source'] == ''

    @pyqtProperty(str, constant=True)
    def name(self):
        return self._data['name']

    @pyqtProperty(str, constant=True)
    def logo(self):
        return self._data['logo']

    @pyqtProperty(float, notify=sizeChanged)
    def size(self):
        if not self.isLocal:
            for arch in self._data['variants'].keys():
                if arch in self._archMap[self.liveUSBData.releaseProxyModel.archFilter]:
                    return self._data['variants'][arch]['size']
        return self._size

    @size.setter
    def size(self, value):
        if self.isLocal and self._size != value:
            self._size = value
            self.sizeChanged.emit()

    @pyqtProperty('QStringList', constant=True)
    def arch(self):
        ret = list()
        for key in self._archMap.keys():
            for variant in self._archMap[key]:
                if variant in self._data['variants'].keys():
                    ret.append(str(key))
        return ret

    @pyqtProperty(str, constant=True)
    def version(self):
        return self._data['version']

    @pyqtProperty(QDateTime, constant=True)
    def releaseDate(self):
        return QDateTime.fromString(self._data['releaseDate'], Qt.ISODate)

    @pyqtProperty(str, constant=True)
    def summary(self):
        return self._data['summary']

    @pyqtProperty(str, constant=True)
    def description(self):
        return self._data['description']

    @pyqtProperty(bool, constant=True)
    def isLocal(self):
        return self._data['source'] == 'Local'

    @pyqtProperty('QStringList', notify=screenshotsChanged)
    def screenshots(self):
        return self._data['screenshots']

    @pyqtProperty(str, constant=True)
    def url(self):
        if not self.isLocal:
            for arch in self._data['variants'].keys():
                if arch in self._archMap[self.liveUSBData.releaseProxyModel.archFilter]:
                    return self._data['variants'][arch]['url']
        return ''

    @pyqtProperty(str, notify=pathChanged)
    def path(self):
        return self._download.path

    @path.setter
    def path(self, value):
        if sys.platform.startswith('win') and value.startswith('file:///'):
            value = value.replace('file:///', '', 1)
        elif not sys.platform.startswith('win') and value.startswith('file://'):
            value = value.replace('file://', '', 1)
        if self._path != value:
            self._download.path = value
            self.pathChanged.emit()
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
            return _('Starting')
        elif self._download.running:
            return _('Downloading')
        elif len(self._error) > 0:
            return _('Error')
        elif self.readyToWrite and not self._writer.running and not self._writer.finished:
            return _('Ready to write')
        elif self._writer.status:
            return self._writer.status
        else:
            return _('Finished')

    @pyqtProperty('QStringList', notify=infoChanged)
    def info(self):
        return self._info

    def addInfo(self, value):
        if value not in self._info:
            self._info.append(value)
            self.infoChanged.emit()

    @pyqtProperty('QStringList', notify=warningChanged)
    def warning(self):
        return self._warning

    def addWarning(self, value):
        if value not in self._warning:
            self._warning.append(value)
            self.warningChanged.emit()

    @pyqtProperty('QStringList', notify=errorChanged)
    def error(self):
        return self._error

    def addError(self, value):
        if value not in self._error:
            self._error.append(str(value))
            self.errorChanged.emit()

class ReleaseListModel(QAbstractListModel):
    """ An abstraction over the list of releases to have them nicely exposed to QML and ready to be filtered
    """
    def __init__(self, parent):
        QAbstractListModel.__init__(self, parent)

    def rowCount(self, parent=QModelIndex()):
        return len(self.parent().releaseData)

    def roleNames(self):
        return {Qt.UserRole + 1 : 'release'}

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            return self.parent().releaseData[index.row()]
        return None

class ReleaseListProxy(QSortFilterProxyModel):
    """ Filtering proxy for the release list
    """
    archChanged = pyqtSignal()
    nameFilterChanged = pyqtSignal()
    isFrontChanged = pyqtSignal()

    _archFilter = ['x86_64']
    _nameFilter = ''
    _frontPage = True

    _archMap = {'64bit': ['x86_64'], '32bit': ['i686','i386']} #, 'ARM': ['armv7hl']}

    def __init__(self, parent, sourceModel):
        QSortFilterProxyModel.__init__(self, parent)
        self.setSourceModel(sourceModel)

    def rowCount(self, parent=QModelIndex()):
        if self._frontPage and self.sourceModel().rowCount(parent) > 3:
            return 3
        return self.sourceModel().rowCount(parent)

    def filterAcceptsRow(self, sourceRow, sourceParent):
        row = self.sourceModel().index(sourceRow, 0, sourceParent).data()
        if len(self._archFilter) == 0 or row.isLocal or self.archFilter in row.arch or row.isSeparator:
            if not len(self._nameFilter) or not row.isSeparator:
                if len(self._nameFilter) == 0 or self._nameFilter.lower() in row.name.lower() or self._nameFilter.lower() in row.summary.lower():
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
        self._archFilter = self._archMap['64bit']
        return '64bit'

    @archFilter.setter
    def archFilter(self, value):
        if self._archMap.has_key(value) and self.archFilter != self._archMap[value]:
            self._archFilter = self._archMap[value]
            self.archChanged.emit()
            self.invalidateFilter()

    @pyqtProperty(bool, notify=isFrontChanged)
    def isFront(self):
        return self._frontPage

    @isFront.setter
    def isFront(self, value):
        if value != self._frontPage:
            self._frontPage = value
            self.isFrontChanged.emit()
            self.invalidate()

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
    """ An entry point to all the exposed properties.
        There is a list of images and USB drives
    """
    releasesChanged = pyqtSignal()
    currentImageChanged = pyqtSignal()
    usbDrivesChanged = pyqtSignal()
    currentDriveChanged = pyqtSignal()
    optionsChanged = pyqtSignal()

    _currentIndex = 0
    _currentDrive = 0

    # man, this is just awkward... but it seems like the only way to do it in a predictable manner without creating a new class
    _optionKeys = ['dd', 'resetMBR'] if not sys.platform.startswith("win") \
              else ['resetMBR']
    _optionNames = {'dd': _('Use <b>dd</b> to write the image - this will erase everything on your portable drive'),
                    'resetMBR': _('Reset the MBR (Master Boot Record)'),
                   }
    _optionValues = {'dd': False,
                     'resetMBR': True,
                    }

    def __init__(self, opts):
        QObject.__init__(self)
        self.live = LiveUSBCreator(opts=opts)
        self._releaseModel = ReleaseListModel(self)
        self._releaseProxy = ReleaseListProxy(self, self._releaseModel)

        self.releaseData = []

        for release in releases:
            self.releaseData.append(Release(self,
                                            len(self.releaseData),
                                            self.live,
                                            release
                                    ))
        self._usbDrives = []
        self.currentDriveChanged.connect(self.currentImage.inspectDestination)

        self.live.detect_removable_drives(callback=self.USBDeviceCallback)


    def USBDeviceCallback(self):
        tmpDrives = []
        previouslySelected = ''
        if len(self._usbDrives) > 0:
            previouslySelected = self._usbDrives[self._currentDrive].drive['device']
        for drive, info in self.live.drives.items():
            name = ''
            if 'friendlyName' in info:
                name = info['friendlyName']
            elif 'label' in info:
                name = info['device'] + ' - ' + info['label']
            else:
                name = info['device']

            gb = 1000.0 # if it's decided to use base 2 values, change this

            if 'fullSize' in info:
                usedSize = info['fullSize']
            else:
                usedSize = info['size']

            if usedSize < gb ** 1:
                name += ' (%.1f B)'  % (usedSize / (gb ** 0))
            elif usedSize < gb ** 2:
                name += ' (%.1f KB)' % (usedSize / (gb ** 1))
            elif usedSize < gb ** 3:
                name += ' (%.1f MB)' % (usedSize / (gb ** 2))
            elif usedSize < gb ** 4:
                name += ' (%.1f GB)' % (usedSize / (gb ** 3))
            else:
                name += ' (%.1f TB)' % (usedSize / (gb ** 4))

            tmpDrives.append(USBDrive(self, name, info))

        if tmpDrives != self._usbDrives:
            self._usbDrives = tmpDrives
            self.usbDrivesChanged.emit()

            self.currentDrive = -1
            for i, drive in enumerate(self._usbDrives):
                if drive.drive['device'] == previouslySelected:
                    self.currentDrive = i
            self.currentDriveChanged.emit()

    @pyqtProperty(ReleaseListModel, notify=releasesChanged)
    def releaseModel(self):
        return self._releaseModel

    @pyqtProperty(ReleaseListProxy, notify=releasesChanged)
    def releaseProxyModel(self):
        return self._releaseProxy

    @pyqtProperty(int, notify=currentImageChanged)
    def currentIndex(self):
        return self._currentIndex

    @currentIndex.setter
    def currentIndex(self, value):
        if value != self._currentIndex:
            self.currentDriveChanged.disconnect(self.currentImage.inspectDestination)
            self._currentIndex = value
            self.currentImageChanged.emit()
            self.currentDriveChanged.connect(self.currentImage.inspectDestination)

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
            self.live.drive = None
            self._currentDrive = -1
            self.currentDriveChanged.emit()
            return
        elif value > len(self._usbDrives):
            value = 0
        if self._currentDrive != value:# or not self.live.drive or self.live.drives[self.live.drive]['device'] != self._usbDrives[value].drive['device']:
            self._currentDrive = value
            if len(self._usbDrives) > 0:
                self.live.drive = self._usbDrives[self._currentDrive].drive['device']
            self.currentDriveChanged.emit()
            for r in self.releaseData:
                r.download.finished = False

    @pyqtProperty('QStringList', constant=True)
    def optionNames(self):
        ret = []
        for i in self._optionKeys:
            ret.append(self._optionNames[i])
        return ret

    @pyqtProperty('QVariant', notify=optionsChanged)
    def optionValues(self):
        ret = []
        for i in self._optionKeys:
            ret.append(self._optionValues[i])
        return ret

    @pyqtSlot(int, bool)
    def setOption(self, index, value):
        key = self._optionKeys[index]
        if self._optionValues[key] != value:
            # dd and resetMBR options are mutually exclusive
            if key == 'dd' and value:
                self._optionValues['resetMBR'] = False
            if key == 'resetMBR' and value:
                self._optionValues['dd'] = False
            self._optionValues[key] = value
            self.optionsChanged.emit()
            self.currentImage.inspectDestination()

    @pyqtSlot()
    def option(self, index):
        return self._optionValues[index]


class LiveUSBApp(QGuiApplication):
    """ Main application class """
    def __init__(self, opts, args):
        QGuiApplication.__init__(self, args)
        translator = QTranslator()
        translator.load(QLocale.system().name(), "po")
        self.installTranslator(translator)
        qmlRegisterUncreatableType(ReleaseDownload, 'LiveUSB', 1, 0, 'Download', 'Not creatable directly, use the liveUSBData instance instead')
        qmlRegisterUncreatableType(ReleaseWriter, 'LiveUSB', 1, 0, 'Writer', 'Not creatable directly, use the liveUSBData instance instead')
        qmlRegisterUncreatableType(ReleaseListModel, 'LiveUSB', 1, 0, 'ReleaseModel', 'Not creatable directly, use the liveUSBData instance instead')
        qmlRegisterUncreatableType(Release, 'LiveUSB', 1, 0, 'Release', 'Not creatable directly, use the liveUSBData instance instead')
        qmlRegisterUncreatableType(USBDrive, 'LiveUSB', 1, 0, 'Drive', 'Not creatable directly, use the liveUSBData instance instead')
        qmlRegisterUncreatableType(LiveUSBData, 'LiveUSB', 1, 0, 'Data', 'Use the liveUSBData root instance')

        engine = QQmlApplicationEngine()
        self.data = LiveUSBData(opts)
        engine.rootContext().setContextProperty('liveUSBData', self.data)
        if (opts.directqml):
            engine.load(QUrl('liveusb/liveusb.qml'))
        else:
            engine.load(QUrl('qrc:/liveusb.qml'))
        engine.rootObjects()[0].show()

        self.exec_()
