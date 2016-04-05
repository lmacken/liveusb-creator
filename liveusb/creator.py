# -*- coding: utf-8 -*-
#
# Copyright © 2008-2015  Red Hat, Inc. All rights reserved.
# Copyright © 2008-2015  Luke Macken <lmacken@redhat.com>
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

"""
Our main LiveUSBCreator module.

This contains the LiveUSBCreator parent class, which is an abstract interface
that provides platform-independent methods.  Platform specific implementations
include the LinuxLiveUSBCreator and the WindowsLiveUSBCreator.
"""

import hashlib
import logging
import os
import signal
import subprocess
import sys
import time
from StringIO import StringIO
from argparse import _AppendAction
from stat import ST_SIZE

from liveusb import _
from liveusb.releases import releases


class LiveUSBError(Exception):
    """ A generic error message that is thrown by the LiveUSBCreator """

    def __init__(self, fullMessage, shortMessage=""):
        self.args = [fullMessage]
        if shortMessage != "":
            self.short = shortMessage
        else:
            self.short = fullMessage


class Drive(object):
    friendlyName = ''
    device = ''
    size = 0
    type = 'usb'  # so far only this, mmc/sd in the future
    mount = []
    isIso9660 = False

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.friendlyName == other.friendlyName
            and self.size == other.size
            and self.type == other.type
            and self.isIso9660 == other.isIso9660)

    def __ne__(self, other):
        return not self.__eq__(other)


class LiveUSBCreator(object):
    """ An OS-independent parent class for Live USB Creators """

    iso = None  # the path to our live image
    drives = {}  # {device: {'label': label, 'mount': mountpoint}}
    dest = None  # the mount point of of our selected drive
    pids = []  # a list of pids of all of our subprocesses
    output = StringIO()  # log subprocess output in case of errors
    isosize = 0  # the size of the selected iso
    _drive = None  # mountpoint of the currently selected drive
    log = None
    callback = None  # Callback for drive changes

    drive = property(fget=lambda self: self.drives[self._drive] if self._drive and len(self.drives) else None,
                     fset=lambda self, d: self._set_drive(d))

    def __init__(self, opts):
        self.opts = opts
        self._setup_logger()

    def _setup_logger(self):
        self.log = logging.getLogger(__name__)
        level = logging.INFO
        if self.opts.verbose:
            level = logging.DEBUG
        self.log.setLevel(level)
        self.handler = logging.StreamHandler()
        self.handler.setLevel(level)
        formatter = logging.Formatter("[%(module)s:%(lineno)s] %(message)s")
        self.handler.setFormatter(formatter)
        self.log.addHandler(self.handler)

    def detect_removable_drives(self, callback=None):
        """ This method should populate self.drives with removable devices """
        raise NotImplementedError

    def verify_iso_md5(self):
        """ Verify the MD5 checksum of the ISO """
        raise NotImplementedError

    def terminate(self):
        """ Terminate any subprocesses that we have spawned """
        raise NotImplementedError

    def popen(self, cmd, passive=False, **kwargs):
        """ A wrapper method for running subprocesses.

        This method handles logging of the command and it's output, and keeps
        track of the pids in case we need to kill them.  If something goes
        wrong, an error log is written out and a LiveUSBError is thrown.

        @param cmd: The commandline to execute.  Either a string or a list.
        @param passive: Enable passive process failure.
        @param kwargs: Extra arguments to pass to subprocess.Popen
        """
        self.log.debug(cmd)
        if isinstance(cmd, unicode):
            cmd = cmd.encode(sys.getfilesystemencoding(), 'replace')
        self.output.write(cmd)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, stdin=subprocess.PIPE,
                                shell=True, **kwargs)
        self.pids.append(proc.pid)
        out, err = proc.communicate()
        if isinstance(out, unicode):
            out = out.encode('utf-8', 'replace')
        if isinstance(err, unicode):
            err = err.encode('utf-8', 'replace')
        self.output.write(out + '\n' + err + '\n')
        if proc.returncode:
            filename = self.write_log()
            if not passive:
                raise LiveUSBError(_("There was a problem executing the "
                                     "following command: %r\n%r\nA more detailed "
                                     "error log has been written to "
                                     "'%r'" % (cmd, err, filename)))
        return proc

    def verify_iso_sha1(self, progress=None):
        """ Verify the SHA1 checksum of our ISO if it is in our release list """
        if not progress:
            class DummyProgress:
                def set_max_progress(self, value): pass

                def update_progress(self, value): pass

            progress = DummyProgress()
        release = self.get_release_from_iso()
        if release:
            progress.set_max_progress(self.isosize / 1024)
            if 'sha1' in release:
                self.log.info(_("Verifying SHA1 checksum of LiveCD image..."))
                algorithm = 'sha1'
                checksum = hashlib.sha1()
            elif 'sha256' in release:
                self.log.info(_("Verifying SHA256 checksum of LiveCD image..."))
                algorithm = 'sha256'
                checksum = hashlib.sha256()
            else:
                return True
            isofile = file(self.iso, 'rb')
            bytesize = 1024 ** 2
            total = 0
            while bytesize:
                data = isofile.read(bytesize)
                checksum.update(data)
                bytesize = len(data)
                total += bytesize
                progress.update_progress(total / 1024)
            isofile.close()
            if checksum.hexdigest() == release[algorithm]:
                return True
            else:
                self.log.info(_("Error: The SHA1 of your Live CD is "
                                "invalid.  You can run this program with "
                                "the --noverify argument to bypass this "
                                "verification check."))
                return False
        else:
            self.log.debug(_('Unknown ISO, skipping checksum verification'))

    def write_log(self):
        """ Write out our subprocess stdout/stderr to a log file """
        tmpdir = os.getenv('TEMP', '/tmp')
        filename = os.path.join(tmpdir, 'liveusb-creator.log')
        out = file(filename, 'a')
        out.write(self.output.getvalue())
        out.close()
        return filename

    def get_release_from_iso(self):
        """ If the ISO is for a known release, return it. """
        isoname = os.path.basename(self.iso)
        for release in releases:
            for arch in release['variants'].keys():
                if arch in release['variants'].keys() and 'url' in release['variants'][arch] and os.path.basename(
                        release['variants'][arch]['url']) == isoname:
                    return release
        return None

    def _set_drive(self, drive):
        if not drive:
            self._drive = None
            return
        if not self.drives.has_key(str(drive)):
            found = False
            for key in self.drives.keys():
                if self.drives[key].device == drive:
                    drive = key
                    found = True
                    break
            if not found:
                raise LiveUSBError(_("Cannot find device %s" % drive))
        self.log.debug("%s selected: %s" % (drive, self.drives[drive]))
        self._drive = drive

    def get_proxies(self):
        """ Return a dictionary of proxy settings """
        return None

    def set_iso(self, iso):
        """ Select the given ISO """
        self.iso = os.path.abspath(self._to_unicode(iso))
        self.isosize = os.stat(self.iso)[ST_SIZE]

    @staticmethod
    def _to_unicode(obj, encoding='utf-8'):
        if hasattr(obj, 'toUtf8'):  # PyQt5.QtCore.QString
            obj = str(obj.toUtf8())
        if isinstance(obj, basestring):
            if not isinstance(obj, unicode):
                obj = unicode(obj, encoding, 'replace')
        return obj

    def flush_buffers(self):
        """ Flush filesystem buffers """
        pass

    def is_admin(self):
        raise NotImplementedError

    def dd_image(self):
        raise NotImplementedError

    def restore_drive(self, d, callback):
        raise NotImplementedError


class LinuxLiveUSBCreator(LiveUSBCreator):
    bus = None  # the dbus.SystemBus
    udisks = None  # the org.freedesktop.UDisks2 dbus.Interface

    def __init__(self, *args, **kw):
        super(LinuxLiveUSBCreator, self).__init__(*args, **kw)

    @staticmethod
    def strify(s):
        return bytearray(s).replace(b'\x00', b'').decode('utf-8')

    def detect_removable_drives(self, callback=None):
        """ Detect all removable USB storage devices using UDisks2 via D-Bus """
        import dbus
        self.callback = callback
        self.drives = {}
        if not self.bus:
            self.bus = dbus.SystemBus()
        udisks_obj = self.bus.get_object("org.freedesktop.UDisks2",
                                         "/org/freedesktop/UDisks2")
        self.udisks = dbus.Interface(udisks_obj, 'org.freedesktop.DBus.ObjectManager')

        def handleAdded(name, device):
            if ('org.freedesktop.UDisks2.Block' in device and
                        'org.freedesktop.UDisks2.Filesystem' not in device and
                        'org.freedesktop.UDisks2.Partition' not in device):
                self.log.debug('Found a block device that is not a partition on %s' % name)
            else:
                return

            blk = device['org.freedesktop.UDisks2.Block']

            if blk['Drive'] == '/':
                self.log.debug('Skipping root drive: %s' % name)
                return

            drive_obj = self.bus.get_object("org.freedesktop.UDisks2", blk['Drive'])
            drive = dbus.Interface(drive_obj, "org.freedesktop.DBus.Properties").GetAll("org.freedesktop.UDisks2.Drive")

            # this is probably the only check we need, including Drive != "/"
            if (not drive[u'Removable'] or
                    drive[u'Optical'] or
                    (drive[u'ConnectionBus'] != 'usb' and
                             drive[u'ConnectionBus'] != 'sdio')):
                self.log.debug(
                        'Skipping a device that is not removable or connected via USB/SD or is optical: %s' % name)
                return

            data = Drive()
            data.device = self.strify(blk['Device'])
            data.size = int(blk['Size'])
            data.friendlyName = str(drive['Vendor']) + ' ' + str(drive['Model'])
            data.isIso9660 = blk['IdType'] == 'iso9660'
            if drive['ConnectionBus'] == 'usb':
                data.type = 'usb'
            else:
                data.type = 'sd'

            # Skip things without a size
            if not data.size and not self.opts.force:
                self.log.debug('Skipping device without size: %s' % device)
                return

            self.drives[str(name)] = data

            if not self.drive and self.opts.console and not self.opts.force:
                self.drive = str(name)

            if self.opts.force == data.device:
                self.drive = str(name)

            if self.callback:
                self.callback()

        def handleRemoved(path, interfaces):
            if self.drives.has_key(path):
                del self.drives[path]

            if self.callback:
                self.callback()

        if not self.opts.console:
            self.bus.add_signal_receiver(handleAdded, "InterfacesAdded", "org.freedesktop.DBus.ObjectManager",
                                         "org.freedesktop.UDisks2", "/org/freedesktop/UDisks2")
            self.bus.add_signal_receiver(handleRemoved, "InterfacesRemoved", "org.freedesktop.DBus.ObjectManager",
                                         "org.freedesktop.UDisks2", "/org/freedesktop/UDisks2")

        for name, device in self.udisks.GetManagedObjects().iteritems():
            handleAdded(name, device)

    def dd_image(self):
        self.log.info(_('Overwriting device with live image'))
        drive = self.drive.device
        cmd = 'dd if="%s" of="%s" bs=1M iflag=direct oflag=direct conv=fdatasync' % (self.iso, drive)
        self.log.debug(_('Running') + ' %s' % cmd)
        self.popen(cmd)

    def terminate(self):
        for pid in self.pids:
            try:
                os.kill(pid, signal.SIGHUP)
                self.log.debug("Killed process %d" % pid)
            except OSError, e:
                self.log.debug(repr(e))

    def verify_iso_md5(self):
        """ Verify the ISO md5sum.

        At the moment this is Linux specific, until we port checkisomd5
        to Windows.
        """
        self.log.info(_('Verifying ISO MD5 checksum'))
        try:
            self.popen('checkisomd5 "%s"' % self.iso)
        except LiveUSBError, e:
            self.log.exception(e)
            self.log.info(_('ISO MD5 checksum verification failed'))
            return False
        self.log.info(_('ISO MD5 checksum passed'))
        return True

    def get_proxies(self):
        """ Return the proxy settings.

        At the moment this implementation only works on KDE, and should
        eventually be expanded to support other platforms as well.
        """
        try:
            from PyQt5 import QtCore
        except ImportError:
            self.log.warning("PyQt5 module not installed; skipping KDE "
                             "proxy detection")
            return
        kioslaverc = QtCore.QDir.homePath() + '/.kde/share/config/kioslaverc'
        if not QtCore.QFile.exists(kioslaverc):
            return {}
        settings = QtCore.QSettings(kioslaverc, QtCore.QSettings.IniFormat)
        settings.beginGroup('Proxy Settings')
        proxies = {}
        # check for KProtocolManager::ManualProxy (the only one we support)
        if settings.value('ProxyType') and settings.value('ProxyType').toInt()[0] == 1:
            httpProxy = settings.value('httpProxy').toString()
            if httpProxy != '':
                proxies['http'] = httpProxy
            ftpProxy = settings.value('ftpProxy').toString()
            if ftpProxy != '':
                proxies['ftp'] = ftpProxy
        return proxies

    def format_device(self):
        """ Format the selected partition as FAT32 """
        self.log.info('Formatting %s as FAT32' % self.drive['device'])
        self.popen('mkfs.vfat -F 32 %s' % self.drive['device'])

    def calculate_device_checksum(self, progress=None):
        """ Calculate the SHA1 checksum of the device """
        self.log.info(_("Calculating the SHA1 of %s" % self.drive['device']))
        if not progress:
            class DummyProgress:
                def set_max_progress(self, value): pass

                def update_progress(self, value): pass

            progress = DummyProgress()
        # Get size of drive
        # progress.set_max_progress(self.isosize / 1024)
        checksum = hashlib.sha1()
        device_name = unicode(self.drive.device)
        device = file(device_name, 'rb')
        bytes = 1024 ** 2
        total = 0
        while bytes:
            data = device.read(bytes)
            checksum.update(data)
            bytes = len(data)
            total += bytes
            progress.update_progress(total / 1024)
        hexdigest = checksum.hexdigest()
        self.log.info("sha1(%s) = %s" % (device_name, hexdigest))
        return hexdigest

    def flush_buffers(self):
        self.popen('sync', passive=True)


    def is_admin(self):
        return os.getuid() == 0

    def restore_drive(self, d, callback):
        import dbus

        if not self.bus:
            self.bus = dbus.SystemBus()

        will_format = None
        will_format_device = None

        for name, device in self.udisks.GetManagedObjects().iteritems():
            if 'org.freedesktop.UDisks2.Block' in device and 'org.freedesktop.UDisks2.Filesystem' in device:
                current_device = self.strify(device['org.freedesktop.UDisks2.Block']['Device'])
                if current_device.startswith(d.device) and device['org.freedesktop.UDisks2.Filesystem']['MountPoints']:
                    obj = self.bus.get_object('org.freedesktop.UDisks2', name)
                    obj.Unmount({'Force': True}, dbus_interface='org.freedesktop.UDisks2.Filesystem')
            if 'org.freedesktop.UDisks2.Block' in device and 'org.freedesktop.UDisks2.PartitionTable' in device:
                current_device = self.strify(device['org.freedesktop.UDisks2.Block']['Device'])
                if current_device == d.device:
                    will_format = name
                    will_format_device = device

        obj = self.bus.get_object('org.freedesktop.UDisks2', will_format)

        create = obj.get_dbus_method('CreatePartition', 'org.freedesktop.UDisks2.PartitionTable')
        clear = obj.get_dbus_method('Format', 'org.freedesktop.UDisks2.Block')

        def error_handler(msg):
            callback(False, msg.get_dbus_message())

        def format_reply_handler():
            callback(True)

        def create_reply_handler(partition):
            obj = self.bus.get_object('org.freedesktop.UDisks2', partition)
            format = obj.get_dbus_method('Format', 'org.freedesktop.UDisks2.Block')
            format.call_async('vfat', {}, reply_handler=format_reply_handler, error_handler=error_handler)

        def clear_reply_handler():
            create.call_async(0, will_format_device['org.freedesktop.UDisks2.Block']['Size'], '', '', {}, reply_handler=create_reply_handler, error_handler=error_handler)

        clear.call_async('dos', {}, reply_handler=clear_reply_handler, error_handler=error_handler)


class MacOsLiveUSBCreator(LiveUSBCreator):
    def detect_removable_drives(self, callback=None):
        """ This method should populate self.drives with removable devices """
        pass

    def verify_filesystem(self):
        """
        Verify the filesystem of our device, setting the volume label
        if necessary.  If something is not right, this method throws a
        LiveUSBError.
        """
        pass

    def verify_iso_md5(self):
        """ Verify the MD5 checksum of the ISO """
        pass

    def terminate(self):
        """ Terminate any subprocesses that we have spawned """
        pass

    def get_proxies(self):
        """ Return a dictionary of proxy settings """
        pass

    def flush_buffers(self):
        """ Flush filesystem buffers """
        pass

    def is_admin(self):
        return os.getuid() == 0


class WindowsLiveUSBCreator(LiveUSBCreator):

    def detect_removable_drives(self, callback=None):
        self.drives = {}
        self.callback = callback

        def detect():
            import wmi
            c = wmi.WMI()
            drives = {}
            for d in c.Win32_DiskDrive():
                if not d.Capabilities or 7 not in d.Capabilities or 'USB' != d.InterfaceType: # does not support removable media
                    continue

                data = Drive()
                data.device = str(d.Index)
                data.friendlyName = unicode(d.Caption).encode('utf-8').replace(' USB Device', '')
                data.size = float(d.Size)

                for p in d.associators('Win32_DiskDriveToDiskPartition'):
                    for l in p.associators('Win32_LogicalDiskToPartition'):
                        data.mount.append(unicode(l.DeviceID).encode('utf-8'))

                data.isIso9660 = not data.mount

                drives[unicode(d.Name).encode('utf-8')] = data

            changed = False
            if self.drives != drives:
                changed = True
            self.drives = drives
            if changed and self.callback:
                self.callback()

        if callback:
            from PyQt5.QtCore import QObject, QTimer, pyqtSlot
            """
            A helper class for the UI to detect the drives periodically, not only when started.
            In contrary to the rest of this code, it utilizes Qt - to be able to use the UI event loop

            TODO: I found no other _clean_ and reliable way to do this. WMI provides some kind of drive and device
            watchers. Those however seem to break the Python interpreter, at least on the Windows machine I use.
            """

            class DriveWatcher(QObject):
                def __init__(self, callback, work):
                    QObject.__init__(self)
                    self.callback = callback
                    self.work = work
                    self.timer = QTimer(self)
                    self.timer.timeout.connect(self.doWork)
                    self.timer.start(2000)

                @pyqtSlot()
                def doWork(self):
                    self.work()

            self.watcher = DriveWatcher(callback, detect)

        detect()

    def dd_image(self, update_function=None):
        import re

        if update_function:
            update_function(-1.0)

        for i in self.drive.mount:
            mountvol = subprocess.Popen(['mountvol', i, '/d'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            mountvol.wait()

        diskpart = subprocess.Popen(['diskpart'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        diskpart.communicate('select disk '+self.drive.device+'\r\nclean\r\nexit')
        diskpart.wait()
        if diskpart.returncode != 0:
            self.log('Diskpart exited with a nonzero status')
            return

        if update_function:
            update_function(0.0)
        dd = subprocess.Popen([(os.path.dirname(sys.argv[0]) if len(os.path.dirname(sys.argv[0])) else os.path.dirname(os.path.realpath(__file__))+'/..')+'/tools/dd.exe',
                               'bs=1M',
                               'if='+self.iso,
                               'of=\\\\.\\PHYSICALDRIVE'+self.drive.device,
                               '--size',
                               '--progress'],
                              shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              bufsize=1,
                              universal_newlines=True)
        if update_function:
            while dd.poll() is None:
                buf = dd.stdout.readline().strip()
                #buf = dd.stdout.read(256)
                r = re.search('^([,0-9]+)', buf)
                if r and len(r.groups()) > 0 and len(r.group(0)) > 0:
                    update_function(float(r.group(0).replace(',', '')) / self.isosize)
        else:
            dd.wait()

    def restore_drive(self, d, callback):

        def restore_drive_work(callback, device):
            import threading
            diskpart = subprocess.Popen(['diskpart'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            diskpart.communicate('select disk '+self.drive.device+'\r\nclean\r\ncreate part pri\r\nselect part 1\r\nformat fs=fat32 quick\r\nassign\r\nexit')
            diskpart.wait()
            callback(True)

        from threading import Thread

        t = Thread(target=restore_drive_work, args=(callback, self.drive.device, ))
        t.start()

        """
        Notes to self:
        To write the image:

        mountvol d: /d

        diskpart <<< "select disk 1
            clean
            exit"

        dd if=image of=\\\\.\\PHYSICALDRIVE1 bs=1M

        To clean the drive:

        diskpart <<< "select disk 1
            clean
            create part pri
            select part 1
            format fs=fat32 quick
            assign
            exit
        """
        pass

    def drive_callback(self):
        self.callback()

    def _get_win32_logicaldisk(self, drive):
        """ Return the Win32_LogicalDisk object for the given drive """
        import win32com.client
        cache = self._win32_logicaldisk.get('drive')
        if cache:
            return cache
        obj = None
        try:
            obj = win32com.client.Dispatch("WbemScripting.SWbemLocator") \
                .ConnectServer(".", "root\cimv2") \
                .ExecQuery("Select * from "
                           "Win32_LogicalDisk where Name = '%s'" %
                           drive)
            if not obj:
                self.log.error(_("Unable to get Win32_LogicalDisk; win32com "
                                 "query did not return any results"))
            else:
                obj = obj[0]
                self._win32_logicaldisk[drive] = obj
        except Exception, e:
            self.log.exception(e)
            self.log.error("Unable to get Win32_LogicalDisk")
        return obj

    def _get_device_size(self, drive):
        """ Return the size of the given drive """
        size = None
        try:
            size = int(self._get_win32_logicaldisk(drive).Size)
            self.log.debug(_("Max size of %s: %d") % (drive, size))
        except Exception, e:
            self.log.exception(e)
            self.log.warning(_("Error getting drive size: %r") % e)
        return size

    def popen(self, cmd, **kwargs):
        import win32process
        if isinstance(cmd, basestring):
            cmd = cmd.split()
        prgmfiles = os.getenv('PROGRAMFILES')
        folder = 'LiveUSB Creator'
        paths = [os.path.join(x, folder) for x in (prgmfiles, prgmfiles + ' (x86)')]
        paths += [os.path.join(os.path.dirname(__file__), '..', '..'), '.', os.path.dirname(sys.argv[0])]
        tool = None
        for path in paths:
            exe = os.path.join(path, 'tools', '%s.exe' % cmd[0])
            if os.path.exists(exe):
                tool = '"%s"' % exe
                break
        else:
            raise LiveUSBError(_("Cannot find") + ' %s.  ' % (cmd[0]) +
                               _("Make sure to extract the entire "
                                 "liveusb-creator zip file before "
                                 "running this program."))
        return LiveUSBCreator.popen(self, ' '.join([tool] + cmd[1:]),
                                    creationflags=win32process.CREATE_NO_WINDOW,
                                    **kwargs)

    def terminate(self):
        """ Terminate any subprocesses that we have spawned """
        import win32api, win32con, pywintypes
        for pid in self.pids:
            try:
                handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE,
                                              False, pid)
                self.log.debug("Terminating process %s" % pid)
                win32api.TerminateProcess(handle, -2)
                win32api.CloseHandle(handle)
            except pywintypes.error:
                pass

    def get_proxies(self):
        proxies = {}
        try:
            import _winreg as winreg
            settings = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                      'Software\\Microsoft\\Windows'
                                      '\\CurrentVersion\\Internet Settings')
            proxy = winreg.QueryValueEx(settings, "ProxyEnable")[0]
            if proxy:
                server = str(winreg.QueryValueEx(settings, 'ProxyServer')[0])
                if ';' in server:
                    for p in server.split(';'):
                        protocol, address = p.split('=')
                        proxies[protocol] = '%s://%s' % (protocol, address)
                else:
                    proxies['http'] = 'http://%s' % server
                    proxies['ftp'] = 'ftp://%s' % server
            settings.Close()
        except Exception, e:
            self.log.warning(_('Unable to detect proxy settings: %r') % e)
        self.log.debug(_('Using proxies: %r') % proxies)
        return proxies

    def verify_iso_md5(self):
        """ Verify the ISO md5sum.

        At the moment this is Linux-only, until we port checkisomd5 to Windows.
        """
        return True

    def calculate_device_checksum(self, progress=None):
        """ Calculate the SHA1 checksum of the device """
        self.log.info(_("Calculating the SHA1 of %s" % self._drive))
        time.sleep(3)
        if not progress:
            class DummyProgress:
                def set_max_progress(self, value): pass

                def update_progress(self, value): pass

            progress = DummyProgress()
        progress.set_max_progress(self.drive['size'])
        checksum = hashlib.sha1()
        device_name = r'\\.\%s' % self.drive['device']
        device = file(device_name, 'rb')
        bytes = 1
        total = 0
        while bytes:
            data = device.read(1024 ** 2)
            checksum.update(data)
            bytes = len(data)
            total += bytes
            progress.update_progress(total)
        hexdigest = checksum.hexdigest()
        self.log.info("sha1(%s) = %s" % (self.drive['device'], hexdigest))
        return hexdigest

    def format_device(self):
        """ Format the selected partition as FAT32 """
        self.log.info('Formatting %s as FAT32' % self.drive['device'])
        self.popen('format /Q /X /y /V:Fedora /FS:FAT32 %s' % self.drive['device'])

    def is_admin(self):
        import pywintypes
        try:
            from win32com.shell import shell
            return shell.IsUserAnAdmin()
        except pywintypes.com_error:
            # Thrown on certain XP installs
            return True
