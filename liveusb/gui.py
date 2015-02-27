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
from PyQt5.QtCore import pyqtProperty, pyqtSlot, QObject, QUrl, QDateTime, pyqtSignal, QThread
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
        for folder in ('Downloads', 'My Documents'):
            if os.path.isdir(os.path.join(home, folder)):
                filename = os.path.join(home, folder, filename)
                break
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
        self._path = ''
        self.runningChanged.emit()
        self.currentChanged.emit()
        self.maximumChanged.emit()
        self.pathChanged.emit()

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
        self._path = iso
        self._running = False
        self.pathChanged.emit()
        self.runningChanged.emit()

    @pyqtSlot(str)
    def childError(self, err):
        self.reset()

    @pyqtSlot(str)
    def run(self):
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

class ReleaseWriterThread(QThread):
    status = pyqtSignal(str)

    _useDD = False

    def __init__(self, live, parent, useDD = False):
        QThread.__init__(self, parent)

        self.live = live
        self.parent = parent
        self._useDD = useDD

    def run(self):
        handler = LiveUSBLogHandler(self.status)
        self.live.log.addHandler(handler)
        now = datetime.now()
        try:
            if self._useDD:
                self.ddImage(handler, now)
            else:
                self.copyImage(handler, now)
        except Exception, e:
            self.status.emit(e.args[0])
            self.status.emit(_("LiveUSB creation failed!"))
            self.live.log.exception(e)

        self.live.log.removeHandler(handler)
        self.progressThread.terminate()

    def ddImage(self, handler, now):
        self.parent.progressBar.setRange(0, 0)
        self.live.dd_image()
        self.live.log.removeHandler(handler)
        duration = str(datetime.now() - now).split('.')[0]
        self.status.emit(_("Complete! (%s)") % duration)
        self.parent.progressBar.setRange(0, 1)
        return

    def copyImage(self, handler, now):
        self.live.verify_filesystem()
        if not self.live.drive['uuid'] and not self.live.label:
            self.status.emit(_("Error: Cannot set the label or obtain "
                          "the UUID of your device.  Unable to continue."))
            self.live.log.removeHandler(handler)
            return

        self.live.check_free_space()

        if not self.parent.opts.noverify:
            # Verify the MD5 checksum inside of the ISO image
            if not self.live.verify_iso_md5():
                self.live.log.removeHandler(handler)
                return

            # If we know about this ISO, and it's SHA1 -- verify it
            release = self.live.get_release_from_iso()
            if release and ('sha1' in release or 'sha256' in release):
                if not self.live.verify_iso_sha1(progressThread=self):
                    self.live.log.removeHandler(handler)
                    return

        # Setup the progress bar
        self.progressThread.set_data(size=self.live.totalsize,
                               drive=self.live.drive['device'],
                               freebytes=self.live.get_free_bytes)
        self.progressThread.start()

        self.live.extract_iso()
        self.live.create_persistent_overlay()
        self.live.update_configs()
        self.live.install_bootloader()
        self.live.bootable_partition()

        if self.parent.opts.device_checksum:
            self.live.calculate_device_checksum(progressThread=self)
        if self.parent.opts.liveos_checksum:
            self.live.calculate_liveos_checksum()

        self.progressThread.stop()

        # Flush all filesystem buffers and unmount
        self.live.flush_buffers()
        self.live.unmount_device()

        duration = str(datetime.now() - now).split('.')[0]
        self.status.emit(_("Complete! (%s)" % duration))

class ReleaseWriter(QObject):
    runningChanged = pyqtSignal()
    currentChanged = pyqtSignal()
    maximumChanged = pyqtSignal()

    _running = False
    _current = -1.0
    _maximum = -1.0

    def __init__(self, parent):
        QObject.__init__(self, parent)
        self._worker = ReleaseWriterThread(parent.live, self)

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

    @pyqtProperty(bool, notify=runningChanged)
    def running(self):
        return self._running

    @pyqtProperty(float, notify=maximumChanged)
    def maxProgress(self):
        return self._maximum

    @pyqtProperty(float, notify=currentChanged)
    def progress(self):
        return self._current


class Release(QObject):
    screenshotsChanged = pyqtSignal()
    pathChanged = pyqtSignal()
    statusChanged = pyqtSignal()

    def __init__(self, parent=None, live=None, name = '', logo = '', size = 0, arch = '', fullName = '', releaseDate = QDateTime(), shortDescription = '', fullDescription = '', isLocal = False, screenshots = [], url=''):
        QObject.__init__(self, parent)

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

        self._download = ReleaseDownload(self)
        self._download.pathChanged.connect(self.pathChanged)

        self._writer = ReleaseWriter(self)

        self._download.runningChanged.connect(self.statusChanged)
        self._writer.runningChanged.connect(self.statusChanged)


    @pyqtSlot()
    def get(self):
        self._download.run()

    @pyqtSlot()
    def write(self):
        self._writer.run()

    @pyqtProperty(str, constant=True)
    def name(self):
        return self._name

    @pyqtProperty(str, constant=True)
    def logo(self):
        return self._logo

    @pyqtProperty(float, constant=True)
    def size(self):
        return self._size

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
        elif self.readyToWrite and not self._writer.running:
            return 'Ready to write'
        elif self._writer.running:
            return 'Writing'
        else:
            return 'Finished'

class LiveUSBLogHandler(logging.Handler):

    def __init__(self, cb):
        logging.Handler.__init__(self)
        self.cb = cb

    def emit(self, record):
        if record.levelname in ('INFO', 'ERROR', 'WARN'):
            self.cb(record.msg)

class USBDrive(QObject):

    def __init__(self, parent, name, path):
        QObject.__init__(self, parent)
        self._name = name
        self._path = path

    @pyqtProperty(str, constant=True)
    def text(self):
        return self._name

    @pyqtProperty(str, constant=True)
    def path(self):
        return self._path

class LiveUSBData(QObject):
    releasesChanged = pyqtSignal()
    currentImageChanged = pyqtSignal()
    usbDrivesChanged = pyqtSignal()
    currentDriveChanged = pyqtSignal()

    _currentIndex = 0
    _currentDrive = 0

    def __init__(self, opts):
        QObject.__init__(self)
        self.live = LiveUSBCreator(opts=opts)
        self.releaseData = [Release(self, self.live, name='Custom OS...', shortDescription='<pick from file chooser>', fullDescription='Here you can choose a OS image from your hard drive to be written to your flash disk', isLocal=True, logo='../../data/icon-folder.svg')]
        for release in releases:
            self.releaseData.append(Release(self,
                                            self.live,
                                            name='Fedora '+release['variant'],
                                            shortDescription='Fedora '+release['variant']+' '+release['version']+(' 64bit' if release['arch']=='x86_64' else ' 32bit'),
                                            arch=release['arch'],
                                            size=release['size'],
                                            url=release['url']
                                    ))
        self._usbDrives = []

        def USBDeviceCallback():
            self._usbDrives = []
            for device, info in self.live.drives.items():
                name = ''
                if info['vendor'] and info['model']:
                    name = info['vendor'] + ' ' + info['model']
                elif info['label']:
                    name = info['label']
                else:
                    name = device

                # TODO for some reason it gives me 4MB for my 4GB drive... and the rounding is off on my 8GB drive
                if info['size']:
                    pass
                    if info['size'] < 1024:
                        name += ' (%d B)' % (info['size'])
                    elif info['size'] < 1024 * 1024:
                        name += ' (%d KB)' % (info['size'] / 1024)
                    elif info['size'] < 1024 * 1024 * 1024:
                        name += ' (%d MB)' % (info['size'] / 1024 / 1024)
                    elif info['size'] < 1024 * 1024 * 1024 * 1024:
                        name += ' (%d GB)' % (info['size'] / 1024 / 1024 / 1024)
                    else:
                        name += ' (%d TB)' % (info['size'] / 1024 / 1024 / 1024 / 1024)

                self._usbDrives.append(USBDrive(self, name, device))
            self.usbDrivesChanged.emit()
        try:
            self.live.detect_removable_drives(callback=USBDeviceCallback)
        except LiveUSBError, e:
            pass # TODO


    @pyqtProperty(QQmlListProperty, notify=releasesChanged)
    def releases(self):
        return QQmlListProperty(Release, self, self.releaseData)

    @pyqtProperty(QQmlListProperty, notify=releasesChanged)
    def titleReleases(self):
        return QQmlListProperty(Release, self, self.releaseData[0:4])

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
        if value != self._currentDrive:
            self._currentDrive = value
            self.currentDriveChanged.emit()


class LiveUSBApp(QApplication):
    """ Main application class """
    def __init__(self, opts, args):
        QApplication.__init__(self, args)
        qmlRegisterUncreatableType(ReleaseDownload, "LiveUSB", 1, 0, "Download", "Not creatable directly, use the liveUSBData instance instead")
        qmlRegisterUncreatableType(ReleaseWriter, "LiveUSB", 1, 0, "Writer", "Not creatable directly, use the liveUSBData instance instead")
        qmlRegisterUncreatableType(Release, "LiveUSB", 1, 0, "Release", "Not creatable directly, use the liveUSBData instance instead")
        qmlRegisterUncreatableType(USBDrive, "LiveUSB", 1, 0, "Drive", "Not creatable directly, use the liveUSBData instance instead")
        qmlRegisterUncreatableType(LiveUSBData, "LiveUSB", 1, 0, "Data", "Use the liveUSBData root instance")
        view = QQmlApplicationEngine()
        self.data = LiveUSBData(opts)
        view.rootContext().setContextProperty("liveUSBData", self.data);
        view.load(QUrl('liveusb/liveusb.qml'))
        view.rootObjects()[0].show()
        self.exec_()
