# -*- coding: utf-8 -*-
#
# Copyright © 2008  Red Hat, Inc. All rights reserved.
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

import os

from time import sleep
from PyQt4 import QtCore, QtGui

from liveusb import LiveUSBCreator
from liveusb.dialog import Ui_Dialog


class LiveUSBApp(QtGui.QApplication):
    """ Main application class.  """
    def __init__(self, args=None):
        QtGui.QApplication.__init__(self, args)
        self.mywindow = LiveUSBDialog()
        self.mywindow.show()
        self.exec_()


class ProgressThread(QtCore.QThread):

    def setData(self, size, drive):
        self.totalsize = size / 1024
        self.drive = drive
        self.orig_free = self.getFreeBytes()
        self.emit(QtCore.SIGNAL("maxprogress(int)"), self.totalsize)

    def getFreeBytes(self):
        import win32file
        (spc, bps, fc, tc) = win32file.GetDiskFreeSpace(self.drive[:-1])
        return fc * (spc * bps)

    def run(self):
        while True:
            free = self.getFreeBytes()
            value = (self.orig_free - free) / 1024
            self.emit(QtCore.SIGNAL("progress(int)"), value)
            if value >= self.totalsize:
               break 
            sleep(5)

    def terminate(self):
        self.emit(QtCore.SIGNAL("progress(int)"), self.totalsize)
        QtCore.QThread.terminate(self)


class LiveUSBThread(QtCore.QThread):

    def __init__(self, live, progress, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.progress = progress
        self.live = live

    def status(self, text):
        self.emit(QtCore.SIGNAL("status(const QString &)"), text)

    def run(self):
        try:
            self.status("Verifying filesystem...")
            self.live.verifyFilesystem()
            self.live.checkFreeSpace()

            self.progress.setData(size=self.live.totalsize,
                                  drive=self.live.drive)
            self.progress.start()

            self.status("Extracting ISO to USB device...")
            self.live.extractISO()
            if self.live.overlay:
                self.status("Creating %d Mb persistent overlay..." %
                            self.live.overlay)
                self.live.createPersistentOverlay()
            self.status("Configuring and installing bootloader...")
            self.live.updateConfigs()
            self.live.installBootloader()
            self.status("Complete!")
        except Exception, e:
            self.status(str(e))
            self.status("LiveUSB creation failed!")
        self.progress.terminate()

    def __del__(self):
        # TODO: kill subprocess threads ?!
        self.wait()


class LiveUSBDialog(QtGui.QDialog, Ui_Dialog):
    """ Our main dialog class """
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        try:
            self.live = LiveUSBCreator()
            self.live.detectRemovableDrives()
            for drive in self.live.drives[::-1]:
                self.driveBox.addItem(drive)
        except Exception, e:
            self.textEdit.setPlainText(str(e))
        self.progressThread = ProgressThread()
        self.liveThread = LiveUSBThread(self.live, self.progressThread)
        self.connectslots()

    def connectslots(self):
        self.connect(self.isoBttn, QtCore.SIGNAL("clicked()"), self.selectfile)
        self.connect(self.burnBttn, QtCore.SIGNAL("clicked()"), self.begin)
        self.connect(self.overlaySlider, QtCore.SIGNAL("valueChanged(int)"),
                     self.overlayValue)
        self.connect(self.liveThread, QtCore.SIGNAL("status(const QString &)"),
                     self.status)
        self.connect(self.liveThread, QtCore.SIGNAL("finished()"),
                     self.unlockUi)
        self.connect(self.liveThread, QtCore.SIGNAL("terminated()"),
                     self.unlockUi)
        self.connect(self.progressThread, QtCore.SIGNAL("progress(int)"),
                     self.progress)
        self.connect(self.progressThread, QtCore.SIGNAL("maxprogress(int)"),
                     self.maxprogress)

    def progress(self, value):
        self.progressBar.setValue(value)

    def maxprogress(self, value):
        self.progressBar.setMaximum(value)

    def status(self, text):
        self.textEdit.append(text)

    def lockUi(self):
        self.burnBttn.setEnabled(False)
        self.overlaySlider.setEnabled(False)
        self.driveBox.setEnabled(False)
        self.isoBttn.setEnabled(False)

    def unlockUi(self):
        self.burnBttn.setEnabled(True)
        self.driveBox.setEnabled(True)
        self.overlaySlider.setEnabled(True)
        self.isoBttn.setEnabled(True)

    def overlayValue(self, value):
        self.overlayTitle.setTitle("Persistent Overlay (%d Mb)" % value)

    def begin(self):
        self.live.drive = str(self.driveBox.currentText())
        self.live.overlay = self.overlaySlider.value()
        self.lockUi()
        self.liveThread.start()

    def selectfile(self):
        isofile = QtGui.QFileDialog.getOpenFileName(self, "Select Live ISO",
                                                    ".", "ISO (*.iso)" )
        if isofile:
            self.live.iso = str(isofile)
            self.textEdit.append(os.path.basename(self.live.iso) + ' selected')
            self.burnBttn.setEnabled(True)

# vim:ts=4 sw=4 expandtab:
