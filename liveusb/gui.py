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
    import dbus.mainloop.qt
    dbus.mainloop.qt.DBusQtMainLoop(set_as_default=True)
except:
    pass

MAX_FAT16 = 2047
MAX_FAT32 = 3999
MAX_EXT = 2097152

class Release(QObject):
    screenshotsChanged = pyqtSignal()

    def __init__(self, parent=None, name = '', logo = '', size = 0, arch = '', fullName = '', releaseDate = QDateTime(), shortDescription = '', fullDescription = '', hasDetails = True, screenshots = [], url=''):
        QObject.__init__(self, parent)

        self._name = name.replace('_', ' ')
        self._logo = logo
        self._size = size
        self._arch = arch
        self._fullName = fullName
        self._releaseDate = releaseDate
        self._shortDescription = shortDescription
        self._fullDescription = fullDescription
        self._hasDetails = hasDetails
        self._screenshots = screenshots
        self._url = url

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

    @pyqtProperty('QDateTime', constant=True)
    def releaseDate(self):
        return self._releaseDate

    @pyqtProperty(str, constant=True)
    def shortDescription(self):
        return self._shortDescription

    @pyqtProperty(str, constant=True)
    def fullDescription(self):
        return self._fullDescription

    @pyqtProperty(bool, constant=True)
    def hasDetails(self):
        return self._hasDetails

    @pyqtProperty(QQmlListProperty, notify=screenshotsChanged)
    def screenshots(self):
        return QQmlListProperty(str, self, self._screenshots)

    @pyqtProperty(str, constant=True)
    def url(self):
        return self._url

class IsoDownloaderThread(QThread):
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

class IsoDownloader(QObject, BaseMeter):
    maxProgressChanged = pyqtSignal()
    progressChanged = pyqtSignal()
    statusChanged = pyqtSignal()
    readyToWriteChanged = pyqtSignal()
    isoPathChanged = pyqtSignal()

    _status = 'Initializing'
    _maximum = -1.0
    _current = -1.0
    _readyToWrite = False
    _isoPath = ''

    """ A QObject urlgrabber BaseMeter class.

    This class is called automatically by urlgrabber with our download details.
    This class then sends signals to our main dialog window to update the
    progress bar.
    """
    def __init__(self, parent, live):
        QObject.__init__(self, parent)

        self._live = live

    def start(self, filename=None, url=None, basename=None, size=None, now=None, text=None):
        self._maximum = size
        self._status = 'Starting'
        self.statusChanged.emit()

    def update(self, amount_read, now=None):
        """ Update our download progressbar.

        :read: the number of bytes read so far
        """
        if self._current < amount_read:
            self._current = amount_read
            self.progressChanged.emit()
        self._status = 'Downloading'
        self.statusChanged.emit()

    def end(self, amount_read):
        self._current = amount_read
        self.progressChanged.emit()

    @pyqtSlot(str)
    def childFinished(self, iso):
        print(iso)
        self._status = 'Ready to write'
        self._maximum = -1.0
        self._current = -1.0
        self._readyToWrite = True
        self._isoPath = iso
        self.statusChanged.emit()
        self.progressChanged.emit()
        self.maxProgressChanged.emit()
        self.readyToWriteChanged.emit()
        self.isoPathChanged.emit()

    @pyqtSlot(str)
    def childError(self, err):
        self._status = 'Error: ' + err
        self._maximum = -1.0
        self._current = -1.0
        self.statusChanged.emit()
        self.progressChanged.emit()
        self.maxProgressChanged.emit()

    @pyqtSlot(str)
    def run(self, url):
        self._grabber = IsoDownloaderThread(url, self, self._live.get_proxies())
        self._grabber.start()
        self._grabber.downloadFinished.connect(self.childFinished)
        self._grabber.downloadError.connect(self.childError)

    @pyqtSlot()
    def cancel(self):
        self._grabber.terminate()
        self._status = 'Initializing...'
        self._maximum = -1.0
        self._current = -1.0
        self._readyToWrite = False
        self._isoPath = ''
        self.statusChanged.emit()
        self.progressChanged.emit()
        self.maxProgressChanged.emit()

    @pyqtProperty(str, notify=statusChanged)
    def status(self):
        return self._status

    @pyqtProperty(float, notify=maxProgressChanged)
    def maxProgress(self):
        return self._maximum

    @pyqtProperty(float, notify=progressChanged)
    def progress(self):
        return self._current

    @pyqtProperty(bool, notify=readyToWriteChanged)
    def readyToWrite(self):
        return self._readyToWrite

    @pyqtProperty(str, notify=isoPathChanged)
    def isoPath(self):
        return self._isoPath

class WriterThread(QThread):

    def __init__(self, live, parent):
        QThread.__init__(self, parent)


class LiveUSBData(QObject):
    releasesChanged = pyqtSignal()
    currentImageChanged = pyqtSignal()

    _currentIndex = 0

    def __init__(self, opts):
        QObject.__init__(self)
        self.live = LiveUSBCreator(opts=opts)
        self._downloader = IsoDownloader(self, self.live)
        self.releaseData = [Release(self, name='Custom OS...', shortDescription='<pick from file chooser>', fullDescription='Here you can choose a OS image from your hard drive to be written to your flash disk', hasDetails=False, logo='../../data/icon-folder.svg')]
        for release in releases:
            self.releaseData.append(Release(self,
                                            name='Fedora '+release['variant'],
                                            shortDescription='Fedora '+release['variant']+' '+release['version']+(' 64bit' if release['arch']=='x86_64' else ' 32bit'),
                                            arch=release['arch'],
                                            size=release['size'],
                                            url=release['url']
                                    ))

    @pyqtProperty(QQmlListProperty, notify=releasesChanged)
    def releases(self):
        return QQmlListProperty(Release, self, self.releaseData)

    @pyqtProperty(QQmlListProperty, notify=releasesChanged)
    def titleReleases(self):
        return QQmlListProperty(Release, self, self.releaseData[0:4])

    @pyqtProperty(IsoDownloader, constant=True)
    def downloader(self):
        return self._downloader

    @pyqtProperty(int, notify=currentImageChanged)
    def currentIndex(self):
        return self._currentIndex

    @currentIndex.setter
    def currentIndex(self, value):
        self._currentIndex = value
        self.currentImageChanged.emit()

    @pyqtProperty(Release, notify=currentImageChanged)
    def currentImage(self):
        return self.releaseData[self._currentIndex]



class LiveUSBApp(QApplication):
    """ Main application class """
    def __init__(self, opts, args):
        QApplication.__init__(self, args)
        qmlRegisterUncreatableType(IsoDownloader, "LiveUSB", 1, 0, "Downloader", "Not creatable directly, use the liveUSBData instance instead")
        qmlRegisterUncreatableType(Release, "LiveUSB", 1, 0, "Release", "Not creatable directly, use the liveUSBData instance instead")
        qmlRegisterUncreatableType(LiveUSBData, "LiveUSB", 1, 0, "Data", "Use the liveUSBData root instance")
        view = QQmlApplicationEngine()
        self.data = LiveUSBData(opts)
        view.rootContext().setContextProperty("liveUSBData", self.data);
        view.load(QUrl('liveusb/liveusb.qml'))
        view.rootObjects()[0].show()
        self.exec_()
