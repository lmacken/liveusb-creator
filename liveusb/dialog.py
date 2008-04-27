# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'data\liveusb-creator.ui'
#
# Created: Sun Apr 27 03:57:43 2008
#      by: PyQt4 UI code generator 4.3.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(QtCore.QSize(QtCore.QRect(0,0,422,388).size()).expandedTo(Dialog.minimumSizeHint()))

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)

        self.startButton = QtGui.QPushButton(Dialog)
        self.startButton.setEnabled(True)
        self.startButton.setGeometry(QtCore.QRect(140,350,131,31))
        self.startButton.setObjectName("startButton")

        self.textEdit = QtGui.QTextEdit(Dialog)
        self.textEdit.setGeometry(QtCore.QRect(10,200,401,111))
        self.textEdit.setReadOnly(True)
        self.textEdit.setObjectName("textEdit")

        self.progressBar = QtGui.QProgressBar(Dialog)
        self.progressBar.setGeometry(QtCore.QRect(10,320,401,23))
        self.progressBar.setProperty("value",QtCore.QVariant(0))
        self.progressBar.setObjectName("progressBar")

        self.downloadGroup = QtGui.QGroupBox(Dialog)
        self.downloadGroup.setGeometry(QtCore.QRect(210,80,201,51))
        self.downloadGroup.setObjectName("downloadGroup")

        self.downloadCombo = QtGui.QComboBox(self.downloadGroup)
        self.downloadCombo.setGeometry(QtCore.QRect(10,20,181,22))
        self.downloadCombo.setObjectName("downloadCombo")

        self.label_2 = QtGui.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(180,100,21,20))

        font = QtGui.QFont()
        font.setFamily("Verdana")
        font.setPointSize(10)
        font.setWeight(75)
        font.setBold(True)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")

        self.groupBox = QtGui.QGroupBox(Dialog)
        self.groupBox.setGeometry(QtCore.QRect(10,80,161,51))
        self.groupBox.setObjectName("groupBox")

        self.isoBttn = QtGui.QPushButton(self.groupBox)
        self.isoBttn.setGeometry(QtCore.QRect(11,18,141,25))
        self.isoBttn.setObjectName("isoBttn")

        self.groupBox_2 = QtGui.QGroupBox(Dialog)
        self.groupBox_2.setGeometry(QtCore.QRect(10,140,191,51))
        self.groupBox_2.setObjectName("groupBox_2")

        self.driveBox = QtGui.QComboBox(self.groupBox_2)
        self.driveBox.setGeometry(QtCore.QRect(10,20,171,20))
        self.driveBox.setObjectName("driveBox")

        self.overlayTitle = QtGui.QGroupBox(Dialog)
        self.overlayTitle.setGeometry(QtCore.QRect(210,140,201,51))
        self.overlayTitle.setObjectName("overlayTitle")

        self.overlaySlider = QtGui.QSlider(self.overlayTitle)
        self.overlaySlider.setGeometry(QtCore.QRect(10,20,181,21))
        self.overlaySlider.setMaximum(2047)
        self.overlaySlider.setOrientation(QtCore.Qt.Horizontal)
        self.overlaySlider.setTickPosition(QtGui.QSlider.NoTicks)
        self.overlaySlider.setObjectName("overlaySlider")

        self.label = QtGui.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(0,0,430,72))
        self.label.setPixmap(QtGui.QPixmap(":/liveusb-header.png"))
        self.label.setObjectName("label")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Fedora LiveUSB Creator", None, QtGui.QApplication.UnicodeUTF8))
        self.startButton.setWhatsThis(QtGui.QApplication.translate("Dialog", "This button will begin the LiveUSB creation process.  This entails optionally downloading a releas (if an existing one wasn\'t selected),  extracting the ISO to the USB device, creating the persistent overlay, and installing the bootloader.", None, QtGui.QApplication.UnicodeUTF8))
        self.startButton.setText(QtGui.QApplication.translate("Dialog", "Create Live USB", None, QtGui.QApplication.UnicodeUTF8))
        self.textEdit.setWhatsThis(QtGui.QApplication.translate("Dialog", "This is the status console, where all messages get written to.", None, QtGui.QApplication.UnicodeUTF8))
        self.progressBar.setWhatsThis(QtGui.QApplication.translate("Dialog", "This is the progress bar that will indicate how far along in the LiveUSB creation process you are", None, QtGui.QApplication.UnicodeUTF8))
        self.downloadGroup.setWhatsThis(QtGui.QApplication.translate("Dialog", "If you do not select an existing Live CD, the selected release will be downloaded for you.", None, QtGui.QApplication.UnicodeUTF8))
        self.downloadGroup.setTitle(QtGui.QApplication.translate("Dialog", "Download Fedora", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Dialog", "or", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setWhatsThis(QtGui.QApplication.translate("Dialog", "This button allows you to browse for an existing Live CD ISO that you have previously downloaded.  If you do not select one, a release will be downloaded for you automatically.", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("Dialog", "Use existing Live CD", None, QtGui.QApplication.UnicodeUTF8))
        self.isoBttn.setText(QtGui.QApplication.translate("Dialog", "Browse", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setWhatsThis(QtGui.QApplication.translate("Dialog", "This is the USB stick that you want to install your Live CD on.  This device must be formatted with the FAT filesystem.", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("Dialog", "Target Device", None, QtGui.QApplication.UnicodeUTF8))
        self.overlayTitle.setWhatsThis(QtGui.QApplication.translate("Dialog", "By allocating extra space on your USB stick for a persistent overlay, you will be able to store data and make permanent modifications to your live operating system.  Without it, you will not be able to save data that will persist after a reboot.", None, QtGui.QApplication.UnicodeUTF8))
        self.overlayTitle.setTitle(QtGui.QApplication.translate("Dialog", "Persistent Overlay (0 Mb)", None, QtGui.QApplication.UnicodeUTF8))

import resources_rc
