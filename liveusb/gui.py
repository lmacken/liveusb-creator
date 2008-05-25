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
import shutil

from time import sleep
from datetime import datetime
from PyQt4 import QtCore, QtGui

from liveusb import LiveUSBCreator, LiveUSBError
from liveusb.dialog import Ui_Dialog
from liveusb.releases import releases
from liveusb.urlgrabber.grabber import URLGrabber, URLGrabError
from liveusb.urlgrabber.progress import BaseMeter


class LiveUSBApp(QtGui.QApplication):
    """ Main application class.  """
    def __init__(self, opts, args):
        QtGui.QApplication.__init__(self, args) 
        self.mywindow = LiveUSBDialog(opts)
        self.mywindow.show()
        self.exec_()
        self.mywindow.terminate()


class ReleaseDownloader(QtCore.QThread):

    def __init__(self, release, progress):
        QtCore.QThread.__init__(self)
        self.release = release
        self.progress = progress 
        for r in releases:
            if r['name'] == str(release):
                self.url = r['url']
                break
        else:
            raise LiveUSBError("Unknown release: %s" % release)

    def run(self):
        self.emit(QtCore.SIGNAL("status(const QString &)"),
                  "Downloading %s..." % os.path.basename(self.url))
        grabber = URLGrabber(progress_obj=self.progress)
        try:
            iso = grabber.urlgrab(self.url, reget='simple')
        except URLGrabError, e:
            self.emit(QtCore.SIGNAL("dlcomplete(const QString &)"), e.strerror)
        else:
            self.emit(QtCore.SIGNAL("dlcomplete(const QString &)"), iso)


class DownloadProgress(QtCore.QObject, BaseMeter):
    """ A QObject urlgrabber BaseMeter class.

    This class is called automatically by urlgrabber with our download details.
    This class then sends signals to our main dialog window to update the
    progress bar.
    """
    def start(self, filename, url, basename, length, **kw):
        self.emit(QtCore.SIGNAL("maxprogress(int)"), length)

    def update(self, read):
        """ Update our download progressbar.

        read - the number of bytes read so far
        """
        self.emit(QtCore.SIGNAL("progress(int)"), read)

    def end(self, read):
        self.update(read)


class ProgressThread(QtCore.QThread):
    """ A thread that monitors the progress of Live USB creation.

    This thread periodically checks the amount of free space left on the 
    given drive and sends a signal to our main dialog window to update the
    progress bar.
    """
    totalsize = 0
    def setData(self, size, drive):
        self.totalsize = size / 1024
        self.drive = drive
        self.orig_free = self.getFreeBytes()
        self.emit(QtCore.SIGNAL("maxprogress(int)"), self.totalsize)

    def getFreeBytes(self):
        import win32file
        (spc, bps, fc, tc) = win32file.GetDiskFreeSpace(self.drive)
        return fc * (spc * bps)

    def run(self):
        while True:
            free = self.getFreeBytes()
            value = (self.orig_free - free) / 1024
            self.emit(QtCore.SIGNAL("progress(int)"), value)
            if value >= self.totalsize:
               break
            sleep(4)

    def terminate(self):
        self.emit(QtCore.SIGNAL("progress(int)"), self.totalsize)
        QtCore.QThread.terminate(self)


class LiveUSBThread(QtCore.QThread):

    def __init__(self, live, progress, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.progress = progress
        self.parent = parent
        self.live = live

    def status(self, text):
        self.emit(QtCore.SIGNAL("status(const QString &)"), text)

    def run(self):
        now = datetime.now()
        try:
            self.status("Verifying filesystem...")
            self.live.verifyFilesystem()
            self.live.checkFreeSpace()

            # If the ISO looks familar, verify it's SHA1SUM
            if self.live.getReleaseFromISO():
                self.status("Verifying SHA1 of LiveCD image...")
                if not self.live.verifyImage(progress=self):
                    self.status("Error: The SHA1 of your Live CD is invalid")
                    return

            self.progress.setData(size=self.live.totalsize,
                                  drive=self.live.drive)
            self.progress.start()

            self.status("Extracting live image to USB device...")
            self.live.extractISO()
            if self.live.overlay:
                self.status("Creating %d Mb persistent overlay..." %
                            self.live.overlay)
                self.live.createPersistentOverlay()
            self.status("Configuring and installing bootloader...")
            self.live.updateConfigs()
            self.live.installBootloader(force=self.parent.opts.force,
                                        safe=self.parent.opts.safe)
            duration = str(datetime.now() - now).split('.')[0]
            self.status("Complete! (%s)" % duration)
        except LiveUSBError, e:
            self.status(str(e))
            self.status("LiveUSB creation failed!")
        self.progress.terminate()

    def setMaxProgress(self, max):
        self.emit(QtCore.SIGNAL("maxprogress(int)"), max)

    def updateProgress(self, value):
        self.emit(QtCore.SIGNAL("progress(int)"), value)

    def __del__(self):
        self.wait()


class LiveUSBDialog(QtGui.QDialog, Ui_Dialog):
    """ Our main dialog class """
    def __init__(self, opts):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        self.opts = opts

        self.live = LiveUSBCreator()
        self.populateReleases()
        self.populateDevices()

        self.progressThread = ProgressThread()
        self.downloadProgress = DownloadProgress()
        self.liveThread = LiveUSBThread(live=self.live,
                                        progress=self.progressThread,
                                        parent=self)
        self.connectslots()
        self.confirmed = False

    def populateDevices(self):
        self.driveBox.clear()
        if self.opts.force:
            self.driveBox.addItem(self.opts.force)
            return
        try:
            self.live.detectRemovableDrives()
            for drive, label in self.live.drives:
                self.driveBox.addItem(label and "%s (%s)" % (label, drive)
                                      or drive)
            self.startButton.setEnabled(True)
        except LiveUSBError, e:
            self.textEdit.setPlainText(str(e))
            self.startButton.setEnabled(False)

    def populateReleases(self):
        for release in self.live.getReleases():
            self.downloadCombo.addItem(release)

    def connectslots(self):
        self.connect(self.isoBttn, QtCore.SIGNAL("clicked()"), self.selectfile)
        self.connect(self.startButton, QtCore.SIGNAL("clicked()"), self.begin)
        self.connect(self.overlaySlider, QtCore.SIGNAL("valueChanged(int)"),
                     self.overlayValue)
        self.connect(self.liveThread, QtCore.SIGNAL("status(const QString &)"),
                     self.status)
        self.connect(self.liveThread, QtCore.SIGNAL("finished()"),
                     lambda: self.enableWidgets(True))
        self.connect(self.liveThread, QtCore.SIGNAL("terminated()"),
                     lambda: self.enableWidgets(True))
        self.connect(self.liveThread, QtCore.SIGNAL("progress(int)"),
                     self.progress)
        self.connect(self.liveThread, QtCore.SIGNAL("maxprogress(int)"),
                     self.maxprogress)
        self.connect(self.progressThread, QtCore.SIGNAL("progress(int)"),
                     self.progress)
        self.connect(self.progressThread, QtCore.SIGNAL("maxprogress(int)"),
                     self.maxprogress)
        self.connect(self.downloadProgress, QtCore.SIGNAL("maxprogress(int)"),
                     self.maxprogress)
        self.connect(self.downloadProgress, QtCore.SIGNAL("progress(int)"),
                     self.progress)
        self.connect(self.refreshDevicesButton, QtCore.SIGNAL("clicked()"),
                     self.populateDevices)

    def progress(self, value):
        self.progressBar.setValue(value)

    def maxprogress(self, value):
        self.progressBar.setMaximum(value)

    def status(self, text):
        self.textEdit.append(text)

    def enableWidgets(self, enabled=True):
        self.startButton.setEnabled(enabled)
        self.driveBox.setEnabled(enabled)
        self.overlaySlider.setEnabled(enabled)
        self.isoBttn.setEnabled(enabled)
        self.downloadCombo.setEnabled(enabled)
        self.refreshDevicesButton.setEnabled(enabled)

    def overlayValue(self, value):
        self.overlayTitle.setTitle("Persistent Overlay (%d Mb)" % value)

    def getSelectedDrive(self):
        drive = str(self.driveBox.currentText()).split()[-1]
        if drive[0] == '(':
            drive = drive[1:-1]
        return drive

    def begin(self):
        self.enableWidgets(False)
        self.live.setDrive(self.getSelectedDrive())
        self.live.setOverlay(self.overlaySlider.value())

        if self.live.existingLiveOS():
            if not self.confirmed:
                self.status("Your device already contains a LiveOS.  If you "
                            "continue, this will be overwritten.")
                if self.live.existingOverlay() and self.overlaySlider.value():
                    self.status("Warning: Creating a new persistent overlay "
                                "will delete your existing one.")
                self.status("Press 'Create Live USB' again if you wish to "
                            "continue.")
                self.confirmed = True
                self.enableWidgets(True)
                return
            else:
                # The user has confirmed that they wish to overwrite their
                # existing Live OS.  Here we delete it first, in order to 
                # accurately calculate progress.
                self.status("Removing existing Live OS...")
                shutil.rmtree(self.live.getLiveOS())

        # If the user has selected an ISO, use it.  If not, download one.
        if self.live.iso:
            self.liveThread.start()
        else:
            self.downloader = ReleaseDownloader(
                    self.downloadCombo.currentText(),
                    progress=self.downloadProgress)
            self.connect(self.downloader,
                         QtCore.SIGNAL("dlcomplete(const QString &)"),
                         self.downloadComplete)
            self.connect(self.downloader,
                         QtCore.SIGNAL("status(const QString &)"),
                         self.status)
            self.downloader.start()

    def downloadComplete(self, iso):
        """ Called by our ReleaseDownloader thread upon completion.

        Upon success, the thread passes in the filename of the downloaded
        release.  If the 'iso' argument is not an existing file, then
        it is assumed that the download failed and 'iso' should contain
        the error message.
        """
        if os.path.exists(iso):
            self.status("Download complete!")
            self.live.iso = str(iso)
            self.liveThread.start()
        else:
            self.status("Download failed: " + iso)
            self.status("You can try again to resume your download")
            self.enableWidgets(True)

    def selectfile(self):
        isofile = QtGui.QFileDialog.getOpenFileName(self, "Select Live ISO",
                                                    ".", "ISO (*.iso)" )
        if isofile:
            self.live.iso = str(isofile)
            self.textEdit.append(os.path.basename(self.live.iso) + ' selected')


    def terminate(self):
        """ Terminate any processes that we have spawned """
        for pid in self.live.pids:
            if hasattr(os, 'kill'):
                os.kill(pid)
            else:
                import win32api, win32con, pywintypes
                try:
                    handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE,
                                                  False, pid)
                    win32api.TerminateProcess(handle, 0)
                    win32api.CloseHandle(handle)
                except pywintypes.error:
                    pass


# vim:ts=4 sw=4 expandtab:
