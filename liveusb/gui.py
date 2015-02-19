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
from PyQt5.QtCore import pyqtProperty, QObject, QUrl, QDateTime, pyqtSignal
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
    nameChanged = pyqtSignal()
    logoChanged = pyqtSignal()
    sizeChanged = pyqtSignal()
    archChanged = pyqtSignal()
    fullNameChanged = pyqtSignal()
    releaseDateChanged = pyqtSignal()
    shortDescriptionChanged = pyqtSignal()
    fullDescriptionChanged = pyqtSignal()
    hasDetailsChanged = pyqtSignal()

    def __init__(self, parent=None, name = '', logo = '', size = 0, arch = '', fullName = '', releaseDate = QDateTime(), shortDescription = '', fullDescription = '', hasDetails = True):
        QObject.__init__(self, parent)

        self._name = name
        self._logo = logo
        self._size = size
        self._arch = arch
        self._fullName = fullName
        self._releaseDate = releaseDate
        self._shortDescription = shortDescription
        self._fullDescription = fullDescription
        self._hasDetails = hasDetails

    @pyqtProperty(str, notify=nameChanged)
    def name(self):
        return self._name

    @pyqtProperty(str, notify=logoChanged)
    def logo(self):
        return self._logo

    @pyqtProperty(int, notify=sizeChanged)
    def size(self):
        return self._size

    @pyqtProperty(str, notify=archChanged)
    def arch(self):
        return self._arch

    @pyqtProperty(str, notify=fullNameChanged)
    def fullName(self):
        return self._fullName

    @pyqtProperty('QDateTime', notify=releaseDateChanged)
    def releaseDate(self):
        return self._releaseDate

    @pyqtProperty(str, notify=shortDescriptionChanged)
    def shortDescription(self):
        return self._shortDescription

    @pyqtProperty(str, notify=fullDescriptionChanged)
    def fullDescription(self):
        return self._fullDescription

    @pyqtProperty(bool, notify=hasDetailsChanged)
    def hasDetails(self):
        return self._hasDetails


class LiveUSBData(QObject):
    releasesChanged = pyqtSignal()

    def __init__(self, opts):
        QObject.__init__(self)
        self.live = LiveUSBCreator(opts=opts)
        self.releaseData = [Release(self, name='Custom OS...', shortDescription='<pick from file chooser>', fullDescription='Here you can choose a OS image from your hard drive to be written to your flash disk', hasDetails=False)]
        for release in releases:
            self.releaseData.append(Release(self,
                                            name='Fedora '+release['variant'],
                                            shortDescription='Fedora '+release['variant']+' '+release['version']+(' 32bit' if release['arch']=='i686' else ' 64bit'),
                                            arch=release['arch']))

    @pyqtProperty(QQmlListProperty, notify=releasesChanged)
    def releases(self):
        return QQmlListProperty(Release, self, self.releaseData)

    @pyqtProperty(QQmlListProperty, notify=releasesChanged)
    def titleReleases(self):
        return QQmlListProperty(Release, self, self.releaseData[0:4])

class LiveUSBApp(QApplication):
    """ Main application class """
    def __init__(self, opts, args):
        QApplication.__init__(self, args)
        qmlRegisterUncreatableType(Release, "LiveUSB", 1, 0, "Release", "Not creatable directly, use the liveUSBData instance instead")
        qmlRegisterUncreatableType(LiveUSBData, "LiveUSB", 1, 0, "Data", "Use the liveUSBData root instance")
        view = QQmlApplicationEngine()
        self.data = LiveUSBData(opts)
        view.rootContext().setContextProperty("liveUSBData", self.data);
        view.load(QUrl('liveusb/liveusb.qml'))
        view.rootObjects()[0].show()
        self.exec_()
