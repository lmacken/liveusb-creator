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

"""
A cross-platform graphical interface for the LiveUSBCreator
"""

import os
import logging

from time import sleep
from datetime import datetime
from PyQt4 import QtCore, QtGui

from liveusb import LiveUSBCreator, LiveUSBError, LiveUSBInterface, _
from liveusb.releases import releases
from liveusb.urlgrabber.grabber import URLGrabber, URLGrabError
from liveusb.urlgrabber.progress import BaseMeter

try:
    import dbus.mainloop.qt
    dbus.mainloop.qt.DBusQtMainLoop(set_as_default=True)
except:
    pass


class LiveUSBApp(QtGui.QApplication):
    """ Main application class """
    def __init__(self, opts, args):
        QtGui.QApplication.__init__(self, args) 
        self.mywindow = LiveUSBDialog(opts)
        self.mywindow.show()
        try:
            self.exec_()
        finally:
            self.mywindow.terminate()


class ReleaseDownloader(QtCore.QThread):

    def __init__(self, release, progress, proxies):
        QtCore.QThread.__init__(self)
        self.release = release
        self.progress = progress
        self.proxies = proxies
        for rel in releases:
            if rel['name'] == str(release):
                self.url = rel['url']
                break
        else:
            raise LiveUSBError(_("Unknown release: %s" % release))

    def run(self):
        self.emit(QtCore.SIGNAL("status(PyQt_PyObject)"),
                  _("Downloading %s..." % os.path.basename(self.url)))
        grabber = URLGrabber(progress_obj=self.progress, proxies=self.proxies)
        try:
            iso = grabber.urlgrab(self.url, reget='simple')
        except URLGrabError, e:
            self.emit(QtCore.SIGNAL("dlcomplete(PyQt_PyObject)"), e.strerror)
        else:
            self.emit(QtCore.SIGNAL("dlcomplete(PyQt_PyObject)"), iso)


class DownloadProgress(QtCore.QObject, BaseMeter):
    """ A QObject urlgrabber BaseMeter class.

    This class is called automatically by urlgrabber with our download details.
    This class then sends signals to our main dialog window to update the
    progress bar.
    """
    def start(self, filename=None, url=None, basename=None, size=None,
              now=None, text=None):
        self.emit(QtCore.SIGNAL("maxprogress(int)"), size)

    def update(self, amount_read, now=None):
        """ Update our download progressbar.

        :read: the number of bytes read so far
        """
        self.emit(QtCore.SIGNAL("progress(int)"), amount_read)

    def end(self, amount_read):
        self.update(amount_read)


class ProgressThread(QtCore.QThread):
    """ A thread that monitors the progress of Live USB creation.

    This thread periodically checks the amount of free space left on the 
    given drive and sends a signal to our main dialog window to update the
    progress bar.
    """
    totalsize = 0
    orig_free = 0
    drive = None
    get_free_bytes = None

    def set_data(self, size, drive, freebytes):
        self.totalsize = size / 1024
        self.drive = drive
        self.get_free_bytes = freebytes
        self.orig_free = self.get_free_bytes()
        self.emit(QtCore.SIGNAL("maxprogress(int)"), self.totalsize)

    def run(self):
        while True:
            free = self.get_free_bytes()
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
        self.emit(QtCore.SIGNAL("status(PyQt_PyObject)"), text)

    def run(self):
        handler = LiveUSBLogHandler(self.status)
        self.live.log.addHandler(handler)
        now = datetime.now()
        try:
            self.live.verify_filesystem()
            if not self.live.drive['uuid'] and not self.live.label:
                self.status(_("Error: Cannot set the label or obtain " 
                              "the UUID of your device.  Unable to continue."))
                return

            self.live.check_free_space()

            if not self.parent.opts.noverify:
                # Verify the MD5 checksum inside of the ISO image
                if not self.live.verify_iso_md5():
                    return

                # If we know about this ISO, and it's SHA1 -- verify it
                release = self.live.get_release_from_iso()
                if release and release['sha1']:
                    if not self.live.verify_iso_sha1(progress=self):
                        return

            # Setup the progress bar
            self.progress.set_data(size=self.live.totalsize,
                                   drive=self.live.drive['device'],
                                   freebytes=self.live.get_free_bytes)
            self.progress.start()

            self.live.extract_iso()
            self.live.create_persistent_overlay()
            self.live.update_configs()
            self.live.install_bootloader()

            duration = str(datetime.now() - now).split('.')[0]
            self.status(_("Complete! (%s)" % duration))
        except LiveUSBError, e:
            self.status(e.message)
            self.status(_("LiveUSB creation failed!"))
        except Exception, e:
            self.status(e.message)
            self.status(_("LiveUSB creation failed!"))
            import traceback
            traceback.print_exc()

        self.live.log.removeHandler(handler)
        self.live.unmount_device()
        self.progress.terminate()

    def set_max_progress(self, maximum):
        self.emit(QtCore.SIGNAL("maxprogress(int)"), maximum)

    def update_progress(self, value):
        self.emit(QtCore.SIGNAL("progress(int)"), value)

    def __del__(self):
        self.wait()


class LiveUSBLogHandler(logging.Handler):

    def __init__(self, cb):
        logging.Handler.__init__(self)
        self.cb = cb

    def emit(self, record):
        if record.levelname in ('INFO', 'ERROR'):
            self.cb(record.msg.encode('utf8', 'replace'))


class LiveUSBDialog(QtGui.QDialog, LiveUSBInterface):
    """ Our main dialog class """
    def __init__(self, opts):
        QtGui.QDialog.__init__(self)
        LiveUSBInterface.__init__(self)
        self.opts = opts
        self.setupUi(self)
        self.live = LiveUSBCreator(opts=opts)
        self.populate_releases()
        self.populate_devices()
        self.downloader = None
        self.progress_thread = ProgressThread()
        self.download_progress = DownloadProgress()
        self.live_thread = LiveUSBThread(live=self.live,
                                         progress=self.progress_thread,
                                         parent=self)
        self.connect_slots()
        self.confirmed = False

        # Intercept all liveusb INFO log messages, and display them in the gui
        self.handler = LiveUSBLogHandler(lambda x: self.textEdit.append(x))
        self.live.log.addHandler(self.handler)

    def populate_devices(self, *args, **kw):
        self.driveBox.clear()
        self.textEdit.clear()
        try:
            self.live.detect_removable_drives()
            for device, info in self.live.drives.items():
                if info['label']:
                    self.driveBox.addItem("%s (%s)" % (device, info['label']))
                else:
                    self.driveBox.addItem(device)
            self.startButton.setEnabled(True)
        except LiveUSBError, e:
            self.textEdit.setPlainText(e.message.encode('utf8'))
            self.startButton.setEnabled(False)

    def populate_releases(self):
        for release in [release['name'] for release in releases]:
            self.downloadCombo.addItem(release)

    def connect_slots(self):
        self.connect(self.isoBttn, QtCore.SIGNAL("clicked()"), self.selectfile)
        self.connect(self.startButton, QtCore.SIGNAL("clicked()"), self.begin)
        self.connect(self.overlaySlider, QtCore.SIGNAL("valueChanged(int)"),
                     self.overlay_value)
        self.connect(self.live_thread, QtCore.SIGNAL("status(PyQt_PyObject)"),
                     self.status)
        self.connect(self.live_thread, QtCore.SIGNAL("finished()"),
                     lambda: self.enable_widgets(True))
        self.connect(self.live_thread, QtCore.SIGNAL("terminated()"),
                     lambda: self.enable_widgets(True))
        self.connect(self.live_thread, QtCore.SIGNAL("progress(int)"),
                     self.progress)
        self.connect(self.live_thread, QtCore.SIGNAL("maxprogress(int)"),
                     self.maxprogress)
        self.connect(self.progress_thread, QtCore.SIGNAL("progress(int)"),
                     self.progress)
        self.connect(self.progress_thread, QtCore.SIGNAL("maxprogress(int)"),
                     self.maxprogress)
        self.connect(self.download_progress, QtCore.SIGNAL("maxprogress(int)"),
                     self.maxprogress)
        self.connect(self.download_progress, QtCore.SIGNAL("progress(int)"),
                     self.progress)
        if hasattr(self, 'refreshDevicesButton'):
            self.connect(self.refreshDevicesButton, QtCore.SIGNAL("clicked()"),
                         self.populate_devices)

        # If we have access to HAL & DBus, intercept some useful signals
        if hasattr(self.live, 'hal'):
            self.live.hal.connect_to_signal('DeviceAdded',
                                            self.populate_devices)
            self.live.hal.connect_to_signal('DeviceRemoved',
                                            self.populate_devices)

    @QtCore.pyqtSignature("QString")
    def on_driveBox_currentIndexChanged(self, drive):
        """ Change the maximum overlay size when each drive is selected.

        This sets the maximum megabyte size of the persistent storage slider
        to the number of free megabytes on the currently selected
        "Target Device".  If the device is not mounted, or if it has more than
        2gigs of free space, set the maximum to 2047mb, which is apparently
        the largest file we can/should store on a vfat partition.
        """
        if not str(drive):
            return
        freespace = self.live.drives[str(drive).split()[0]]['free']
        if not freespace or freespace > 2047:
            freespace = 2047
        self.overlaySlider.setMaximum(freespace)

    def progress(self, value):
        self.progressBar.setValue(value)

    def maxprogress(self, value):
        self.progressBar.setMaximum(value)

    def status(self, text):
        self.textEdit.append(text.encode('utf8', 'replace'))

    def enable_widgets(self, enabled=True):
        self.startButton.setEnabled(enabled)
        self.driveBox.setEnabled(enabled)
        self.overlaySlider.setEnabled(enabled)
        self.isoBttn.setEnabled(enabled)
        self.downloadCombo.setEnabled(enabled)
        if hasattr(self, 'refreshDevicesButton'):
            self.refreshDevicesButton.setEnabled(enabled)

    def overlay_value(self, value):
        self.overlayTitle.setTitle(_("Persistent Storage") + " (%d MB)" % value)

    def get_selected_drive(self):
        return str(self.driveBox.currentText()).split()[0]

    def begin(self):
        self.enable_widgets(False)
        self.live.overlay = self.overlaySlider.value()
        self.live.drive = self.get_selected_drive()
        try:
            self.live.mount_device()
        except LiveUSBError, e:
            self.status(e.message)
            self.enable_widgets(True)
            return 

        if self.live.existing_liveos():
            if not self.confirmed:
                self.status(_("Your device already contains a LiveOS.\nIf you "
                              "continue, this will be overwritten."))
                if self.live.existing_overlay() and self.overlaySlider.value():
                    self.status(_("Warning: Creating a new persistent overlay "
                                  "will delete your existing one."))
                self.status(_("Press 'Create Live USB' again if you wish to "
                              "continue."))
                self.confirmed = True
                self.live.unmount_device()
                self.enable_widgets(True)
                return
            else:
                # The user has confirmed that they wish to overwrite their
                # existing Live OS.  Here we delete it first, in order to 
                # accurately calculate progress.
                try:
                    self.live.delete_liveos()
                except LiveUSBError, e:
                    self.status(e.message)
                    self.live.unmount_device()
                    self.enable_widgets(True)
                    return

        # Remove the log handler, because our live thread will register its own
        self.live.log.removeHandler(self.handler)

        # If the user has selected an ISO, use it.  If not, download one.
        if self.live.iso:
            self.live_thread.start()
        else:
            self.downloader = ReleaseDownloader(
                    self.downloadCombo.currentText(),
                    progress=self.download_progress,
                    proxies=self.live.get_proxies())
            self.connect(self.downloader,
                         QtCore.SIGNAL("dlcomplete(PyQt_PyObject)"),
                         self.download_complete)
            self.connect(self.downloader,
                         QtCore.SIGNAL("status(PyQt_PyObject)"),
                         self.status)
            self.downloader.start()

    def download_complete(self, iso):
        """ Called by our ReleaseDownloader thread upon completion.

        Upon success, the thread passes in the filename of the downloaded
        release.  If the 'iso' argument is not an existing file, then
        it is assumed that the download failed and 'iso' should contain
        the error message.
        """
        if os.path.exists(iso):
            self.status(_("Download complete!"))
            self.live.iso = iso
            self.live_thread.start()
        else:
            self.status(_("Download failed: " + iso))
            self.status(_("You can try again to resume your download"))
            self.enable_widgets(True)

    def selectfile(self):
        isofile = QtGui.QFileDialog.getOpenFileName(self, _("Select Live ISO"),
                                                    ".", "ISO (*.iso)" )
        if isofile:
            try:
                self.live.iso = self._to_unicode(isofile)
            except Exception, e:
                self.live.log.error(e.message.encode('utf8'))
                self.status(_("Sorry, I'm having trouble encoding the filename "
                              "of your livecd.  You may have better luck if "
                              "you move your ISO to the root of your drive "
                              "(ie: C:\)"))

            self.live.log.info('%s ' % os.path.basename(self.live.iso) + 
                               _("selected"))

    def terminate(self):
        """ Terminate any processes that we have spawned """
        self.live.terminate()

    def _to_unicode(self, obj, encoding='utf-8'):
        if hasattr(obj, 'toUtf8'): # PyQt4.QtCore.QString
            obj = str(obj.toUtf8())
        if isinstance(obj, basestring):
            if not isinstance(obj, unicode):
                obj = unicode(obj, encoding, 'replace')
        return obj
