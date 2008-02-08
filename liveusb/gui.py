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

from luDialog import Ui_luDialog
from liveusb import LiveUSBCreator
from PyQt4 import QtCore, QtGui

class LiveUSBApp(QtGui.QApplication):
    """ Main application class.  """
    def __init__(self, args=None):
        QtGui.QApplication.__init__(self, args)
        self.mywindow = lsUI()
        self.mywindow.show()
        self.exec_()

class lsUI(Ui_luDialog, QtGui.QDialog):
    """ Our main dialog class """
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        try:
            self.live = LiveUSBCreator()
            self.live.detectRemovableDrives()
            for drive in self.live.drives:
                self.driveBox.addItem(drive)
        except Exception, e:
            self.textEdit.setPlainText(str(e))
        self.connectslots()

    def connectslots(self):
        self.connect(self.isoBttn, QtCore.SIGNAL("clicked()"), self.selectfile)
        self.connect(self.burnBttn, QtCore.SIGNAL("clicked()"), self.burn)

    def burn(self):
        self.live.drive = str(self.driveBox.currentText())
        if self.live.iso == None:
            self.textEdit.setPlainText("Please select an ISO first")
            return
        try:
            self.live.verifyFilesystem()
            self.live.extractISO()
            self.live.updateConfigs()
            self.live.installBootloader()
            self.textEdit.setPlainText("Done :)")
        except Exception, e:
            self.textEdit.setPlainText(str(e))

    def selectfile(self):
        isofile = QtGui.QFileDialog.getOpenFileName(self, "Select Live ISO",
                                                    ".", "ISO (*.iso)" )
        self.live.iso = str(isofile)
