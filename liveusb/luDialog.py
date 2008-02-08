# -*- coding: utf-8 -*-
# Form implementation generated from reading ui file 'luDialog.ui'
#
# Created: Mon Feb 04 15:41:02 2008
#      by: PyQt4 UI code generator 4.3.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_luDialog(object):
    def setupUi(self, luDialog):
        luDialog.setObjectName("luDialog")
        luDialog.resize(QtCore.QSize(QtCore.QRect(0,0,384,359).size()).expandedTo(luDialog.minimumSizeHint()))

        self.gridlayout = QtGui.QGridLayout(luDialog)
        self.gridlayout.setObjectName("gridlayout")

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setObjectName("hboxlayout")

        self.isoBttn = QtGui.QPushButton(luDialog)
        self.isoBttn.setObjectName("isoBttn")
        self.hboxlayout.addWidget(self.isoBttn)

        self.label = QtGui.QLabel(luDialog)
        self.label.setObjectName("label")
        self.hboxlayout.addWidget(self.label)

        self.driveBox = QtGui.QComboBox(luDialog)
        self.driveBox.setObjectName("driveBox")
        self.hboxlayout.addWidget(self.driveBox)
        self.gridlayout.addLayout(self.hboxlayout,0,0,1,1)

        spacerItem = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem,1,0,1,1)

        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setObjectName("hboxlayout1")

        spacerItem1 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout1.addItem(spacerItem1)

        self.burnBttn = QtGui.QPushButton(luDialog)
        self.burnBttn.setObjectName("burnBttn")
        self.hboxlayout1.addWidget(self.burnBttn)

        spacerItem2 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout1.addItem(spacerItem2)
        self.gridlayout.addLayout(self.hboxlayout1,2,0,1,1)

        spacerItem3 = QtGui.QSpacerItem(20,16,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem3,3,0,1,1)

        self.textEdit = QtGui.QTextEdit(luDialog)
        self.textEdit.setObjectName("textEdit")
        self.gridlayout.addWidget(self.textEdit,4,0,1,1)

        self.retranslateUi(luDialog)
        QtCore.QMetaObject.connectSlotsByName(luDialog)

    def retranslateUi(self, luDialog):
        luDialog.setWindowTitle(QtGui.QApplication.translate("luDialog", "Fedora Live ISO to USB ", None, QtGui.QApplication.UnicodeUTF8))
        self.isoBttn.setText(QtGui.QApplication.translate("luDialog", "Select The ISO", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("luDialog", "Select Drive to Install", None, QtGui.QApplication.UnicodeUTF8))
        self.burnBttn.setText(QtGui.QApplication.translate("luDialog", "BURN", None, 
            QtGui.QApplication.UnicodeUTF8))
