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

"""
A cross-platform graphical interface for the LiveUSBCreator
"""

import os
import sys
import logging
import urlparse

from time import sleep
from datetime import datetime
from PyQt5.QtCore import pyqtProperty, QObject, QUrl
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQml import qmlRegisterType, QQmlComponent, QQmlApplicationEngine
from PyQt5.QtQuick import QQuickView

from liveusb import LiveUSBCreator, LiveUSBError, LiveUSBInterface, _
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


class LiveUSBApp(QApplication):
    """ Main application class """
    def __init__(self, opts, args):
        QApplication.__init__(self, args)
        view = QQmlApplicationEngine()
        view.load(QUrl('liveusb/liveusb.qml'))
        view.rootObjects()[0].show()
        self.exec_()
