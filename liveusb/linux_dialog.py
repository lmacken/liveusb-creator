# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'data/liveusb-creator.ui'
#
# Created: Tue Jan 15 12:09:54 2013
#      by: PyQt4 UI code generator 4.9.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(422, 388)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.startButton = QtGui.QPushButton(Dialog)
        self.startButton.setEnabled(True)
        self.startButton.setGeometry(QtCore.QRect(130, 350, 158, 34))
        self.startButton.setObjectName(_fromUtf8("startButton"))
        self.textEdit = QtGui.QTextEdit(Dialog)
        self.textEdit.setGeometry(QtCore.QRect(10, 200, 401, 111))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.textEdit.setFont(font)
        self.textEdit.setReadOnly(True)
        self.textEdit.setObjectName(_fromUtf8("textEdit"))
        self.progressBar = QtGui.QProgressBar(Dialog)
        self.progressBar.setGeometry(QtCore.QRect(10, 320, 401, 23))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.downloadGroup = QtGui.QGroupBox(Dialog)
        self.downloadGroup.setGeometry(QtCore.QRect(210, 80, 201, 51))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.downloadGroup.setFont(font)
        self.downloadGroup.setObjectName(_fromUtf8("downloadGroup"))
        self.downloadCombo = QtGui.QComboBox(self.downloadGroup)
        self.downloadCombo.setGeometry(QtCore.QRect(10, 20, 161, 22))
        self.downloadCombo.setObjectName(_fromUtf8("downloadCombo"))
        self.refreshReleasesButton = QtGui.QPushButton(self.downloadGroup)
        self.refreshReleasesButton.setGeometry(QtCore.QRect(170, 20, 30, 20))
        self.refreshReleasesButton.setText(_fromUtf8(""))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/refresh.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.refreshReleasesButton.setIcon(icon)
        self.refreshReleasesButton.setFlat(True)
        self.refreshReleasesButton.setObjectName(_fromUtf8("refreshReleasesButton"))
        self.label_2 = QtGui.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(180, 100, 23, 24))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Verdana"))
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.groupBox = QtGui.QGroupBox(Dialog)
        self.groupBox.setGeometry(QtCore.QRect(10, 80, 161, 51))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.groupBox.setFont(font)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.isoBttn = QtGui.QPushButton(self.groupBox)
        self.isoBttn.setGeometry(QtCore.QRect(11, 18, 141, 25))
        self.isoBttn.setObjectName(_fromUtf8("isoBttn"))
        self.groupBox_2 = QtGui.QGroupBox(Dialog)
        self.groupBox_2.setGeometry(QtCore.QRect(10, 140, 191, 51))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.groupBox_2.setFont(font)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.driveBox = QtGui.QComboBox(self.groupBox_2)
        self.driveBox.setGeometry(QtCore.QRect(10, 20, 151, 21))
        self.driveBox.setEditable(False)
        self.driveBox.setInsertPolicy(QtGui.QComboBox.InsertAtTop)
        self.driveBox.setDuplicatesEnabled(False)
        self.driveBox.setObjectName(_fromUtf8("driveBox"))
        self.refreshDevicesButton = QtGui.QPushButton(self.groupBox_2)
        self.refreshDevicesButton.setGeometry(QtCore.QRect(160, 20, 30, 20))
        self.refreshDevicesButton.setText(_fromUtf8(""))
        self.refreshDevicesButton.setIcon(icon)
        self.refreshDevicesButton.setFlat(True)
        self.refreshDevicesButton.setObjectName(_fromUtf8("refreshDevicesButton"))
        self.overlayTitle = QtGui.QGroupBox(Dialog)
        self.overlayTitle.setGeometry(QtCore.QRect(210, 140, 201, 51))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.overlayTitle.setFont(font)
        self.overlayTitle.setObjectName(_fromUtf8("overlayTitle"))
        self.overlaySlider = QtGui.QSlider(self.overlayTitle)
        self.overlaySlider.setGeometry(QtCore.QRect(10, 20, 181, 21))
        self.overlaySlider.setMaximum(2047)
        self.overlaySlider.setOrientation(QtCore.Qt.Horizontal)
        self.overlaySlider.setTickPosition(QtGui.QSlider.NoTicks)
        self.overlaySlider.setObjectName(_fromUtf8("overlaySlider"))
        self.label = QtGui.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(0, 0, 430, 72))
        self.label.setText(_fromUtf8(""))
        self.label.setPixmap(QtGui.QPixmap(_fromUtf8(":/liveusb-header.png")))
        self.label.setObjectName(_fromUtf8("label"))

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Fedora LiveUSB Creator", None))
        self.startButton.setWhatsThis(_translate("Dialog", "This button will begin the LiveUSB creation process.  This entails optionally downloading a release (if an existing one wasn\'t selected),  extracting the ISO to the USB device, creating the persistent overlay, and installing the bootloader.", None))
        self.startButton.setText(_translate("Dialog", "Create Live USB", None))
        self.textEdit.setWhatsThis(_translate("Dialog", "This is the status console, where all messages get written to.", None))
        self.progressBar.setWhatsThis(_translate("Dialog", "This is the progress bar that will indicate how far along in the LiveUSB creation process you are", None))
        self.downloadGroup.setWhatsThis(_translate("Dialog", "If you do not select an existing Live CD, the selected release will be downloaded for you.", None))
        self.downloadGroup.setTitle(_translate("Dialog", "Download Fedora", None))
        self.label_2.setText(_translate("Dialog", "or", None))
        self.groupBox.setWhatsThis(_translate("Dialog", "This button allows you to browse for an existing Live CD ISO that you have previously downloaded.  If you do not select one, a release will be downloaded for you automatically.", None))
        self.groupBox.setTitle(_translate("Dialog", "Use existing Live CD", None))
        self.isoBttn.setText(_translate("Dialog", "Browse", None))
        self.isoBttn.setShortcut(_translate("Dialog", "Alt+B", None))
        self.groupBox_2.setWhatsThis(_translate("Dialog", "This is the USB stick that you want to install your Live CD on.  This device must be formatted with the FAT filesystem.", None))
        self.groupBox_2.setTitle(_translate("Dialog", "Target Device", None))
        self.overlayTitle.setWhatsThis(_translate("Dialog", "By allocating extra space on your USB stick for a persistent overlay, you will be able to store data and make permanent modifications to your live operating system.  Without it, you will not be able to save data that will persist after a reboot.", "comment!"))
        self.overlayTitle.setTitle(_translate("Dialog", "Persistent Storage (0 MB)", None))

import resources_rc
