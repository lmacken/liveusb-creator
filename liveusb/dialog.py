# -*- coding: utf-8 -*-
#
# Form implementation generated from reading ui file 'data/newdialog.ui'
#
# Created: Thu Apr 10 13:07:21 2008
#      by: PyQt4 UI code generator 4.3.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(QtCore.QSize(QtCore.QRect(0,0,361,274).size()).expandedTo(Dialog.minimumSizeHint()))

        self.gridLayout = QtGui.QWidget(Dialog)
        self.gridLayout.setGeometry(QtCore.QRect(0,40,211,71))
        self.gridLayout.setObjectName("gridLayout")

        self.gridlayout = QtGui.QGridLayout(self.gridLayout)
        self.gridlayout.setObjectName("gridlayout")

        self.overlayTitle = QtGui.QGroupBox(self.gridLayout)
        self.overlayTitle.setObjectName("overlayTitle")

        self.overlaySlider = QtGui.QSlider(self.overlayTitle)
        self.overlaySlider.setGeometry(QtCore.QRect(10,20,171,21))
        self.overlaySlider.setMaximum(2047)
        self.overlaySlider.setOrientation(QtCore.Qt.Horizontal)
        self.overlaySlider.setTickPosition(QtGui.QSlider.NoTicks)
        self.overlaySlider.setObjectName("overlaySlider")
        self.gridlayout.addWidget(self.overlayTitle,0,0,1,1)

        self.layoutWidget = QtGui.QWidget(Dialog)
        self.layoutWidget.setGeometry(QtCore.QRect(0,0,361,41))
        self.layoutWidget.setObjectName("layoutWidget")

        self.hboxlayout = QtGui.QHBoxLayout(self.layoutWidget)
        self.hboxlayout.setObjectName("hboxlayout")

        self.isoBttn = QtGui.QPushButton(self.layoutWidget)
        self.isoBttn.setObjectName("isoBttn")
        self.hboxlayout.addWidget(self.isoBttn)

        self.label = QtGui.QLabel(self.layoutWidget)
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.hboxlayout.addWidget(self.label)

        self.driveBox = QtGui.QComboBox(self.layoutWidget)
        self.driveBox.setObjectName("driveBox")
        self.hboxlayout.addWidget(self.driveBox)

        self.burnBttn = QtGui.QPushButton(Dialog)
        self.burnBttn.setEnabled(False)
        self.burnBttn.setGeometry(QtCore.QRect(220,60,131,41))
        self.burnBttn.setObjectName("burnBttn")

        self.textEdit = QtGui.QTextEdit(Dialog)
        self.textEdit.setGeometry(QtCore.QRect(10,120,341,111))
        self.textEdit.setReadOnly(True)
        self.textEdit.setObjectName("textEdit")

        self.progressBar = QtGui.QProgressBar(Dialog)
        self.progressBar.setGeometry(QtCore.QRect(10,240,351,23))
        self.progressBar.setProperty("value",QtCore.QVariant(0))
        self.progressBar.setObjectName("progressBar")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Fedora LiveUSB Creator", None, QtGui.QApplication.UnicodeUTF8))
        self.overlayTitle.setTitle(QtGui.QApplication.translate("Dialog", "Persistent Overlay (0 Mb)", None, QtGui.QApplication.UnicodeUTF8))
        self.isoBttn.setText(QtGui.QApplication.translate("Dialog", "Select an ISO", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Dialog", "Select Drive to Install", None, QtGui.QApplication.UnicodeUTF8))
        self.burnBttn.setText(QtGui.QApplication.translate("Dialog", "Create Live USB", None, QtGui.QApplication.UnicodeUTF8))

