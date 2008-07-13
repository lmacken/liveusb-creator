# -*- coding: utf-8 -*-
#
# Copyright © 2008  Red Hat, Inc. All rights reserved.
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

"""
Our main LiveUSBCreator module.

This contains the LiveUSBCreator parent class, which is an abstract interface
that provides platform-independent methods.  Platform specific implementations
include the LinuxLiveUSBCreator and the WindowsLiveUSBCreator.
"""

import subprocess
import tempfile
import logging
import shutil
import sha
import os
import re

from StringIO import StringIO
from stat import ST_SIZE

from liveusb.releases import releases


class LiveUSBError(Exception):
    """ A generic error message that is thrown by the LiveUSBCreator """


class LiveUSBCreator(object):
    """ An OS-independent parent class for Live USB Creators """

    iso = None          # the path to our live image
    label = "FEDORA"    # if one doesn't already exist
    fstype = None       # the format of our usb stick
    drives = {}         # {device: {'label': label, 'mount': mountpoint}}
    overlay = 0         # size in mb of our persisten overlay
    dest = None         # the mount point of of our selected drive
    uuid = None         # the uuid of our selected drive
    pids = []           # a list of pids of all of our subprocesses
    output = StringIO() # log subprocess output in case of errors
    totalsize = 0       # the total size of our overlay + iso
    isosize = 0         # the size of the selected iso
    _drive = None       # mountpoint of the currently selected drive
    log = None

    drive = property(fget=lambda self: self.drives[self._drive],
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
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = logging.Formatter("[%(module)s:%(lineno)s] %(message)s")
        handler.setFormatter(formatter)
        self.log.addHandler(handler)

    def detect_removable_drives(self):
        """ This method should populate self.drives with removable devices """
        raise NotImplementedError

    def verify_filesystem(self):
        """
        Verify the filesystem of our device, setting the volume label
        if necessary.  If something is not right, this method throws a
        LiveUSBError.
        """
        raise NotImplementedError

    def get_free_bytes(self, drive=None):
        """ Return the number of free bytes on a given drive.

        If drive is None, then use the currently selected device.
        """
        raise NotImplementedError

    def extract_iso(self):
        """ Extract the LiveCD ISO to the USB drive """
        raise NotImplementedError

    def install_bootloader(self):
        """ Install the bootloader to our device, using syslinux.

        At this point, we can assume that extract_iso has already run, and
        that there is an 'isolinux' directory on our device.
        """
        raise NotImplementedError

    def terminate(self):
        """ Terminate any subprocesses that we have spawned """
        raise NotImplementedError

    def mount_device(self):
        """ Mount self.drive, setting the mount point to self.mount """
        raise NotImplementedError

    def unmount_device(self):
        """ Unmount the device mounted at self.mount """
        raise NotImplementedError

    def popen(self, cmd, **kwargs):
        """ A wrapper method for running subprocesses.

        This method handles logging of the command and it's output, and keeps
        track of the pids in case we need to kill them.  If something goes
        wrong, an error log is written out and a LiveUSBError is thrown.

        @param cmd: The commandline to execute.  Either a string or a list.
        @param kwargs: Extra arguments to pass to subprocess.Popen
        """
        self.log.info(cmd)
        self.output.write(cmd)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, stdin=subprocess.PIPE,
                                shell=True, **kwargs)
        self.pids.append(proc.pid)
        out, err = proc.communicate()
        self.output.write(out + '\n' + err + '\n')
        if proc.returncode:
            self.write_log()
            raise LiveUSBError("There was a problem executing the following "
                               "command: `%s`\nA more detailed error log has "
                               "been written to 'liveusb-creator.log'" % cmd)
        return proc

    def verify_image(self, progress=None):
        """ Verify the SHA1 checksum of our ISO if it is in our release list """
        if not progress:
            class DummyProgress:
                def set_max_progress(self, value): pass
                def update_progress(self, value): pass
            progress = DummyProgress()
        release = self.get_release_from_iso()
        if release:
            progress.set_max_progress(self.isosize / 1024)
            checksum = sha.new()
            isofile = file(self.iso, 'rb')
            bytes = 1024**2
            total = 0
            while bytes:
                data = isofile.read(bytes)
                checksum.update(data)
                bytes = len(data)
                total += bytes
                progress.update_progress(total / 1024)
            return checksum.hexdigest() == release['sha1']

    def check_free_space(self):
        """ Make sure there is enough space for the LiveOS and overlay """
        freebytes = self.get_free_bytes()
        self.log.debug('freebytes = %d' % freebytes)
        self.isosize = os.stat(self.iso)[ST_SIZE]
        self.log.debug('isosize = %d' % self.isosize)
        overlaysize = self.overlay * 1024**2
        self.log.debug('overlaysize = %d' % overlaysize)
        self.totalsize = overlaysize + self.isosize
        if self.totalsize > freebytes:
            raise LiveUSBError("Not enough free space on device.\n"
                               "%dMB ISO + %dMB overlay > %dMB free space" % 
                               (self.isosize/1024**2, self.overlay,
                                freebytes/1024**2))

    def create_persistent_overlay(self):
        if self.overlay:
            self.log.info("Creating %sMB persistent overlay" % self.overlay)
            if self.fstype == 'vfat':
                # vfat apparently can't handle sparse files
                self.popen('dd if=/dev/zero of=%s count=%d bs=1M'
                           % (self.get_overlay(), self.overlay))
            else:
                self.popen('dd if=/dev/zero of=%s count=1 bs=1M seek=%d'
                           % (self.get_overlay(), self.overlay))

    def update_configs(self):
        """ Generate our syslinux.cfg """
        isolinux = file(os.path.join(self.dest, "isolinux", "isolinux.cfg"),'r')
        syslinux = file(os.path.join(self.dest, "isolinux", "syslinux.cfg"),'w')
        usblabel = self.uuid and 'UUID=' + self.uuid or 'LABEL=' + self.label
        for line in isolinux.readlines():
            if "CDLABEL" in line:
                line = re.sub("CDLABEL=[^ ]*", usblabel, line)
                line = re.sub("rootfstype=[^ ]*",
                              "rootfstype=%s" % self.fstype,
                              line)
            if self.overlay and "liveimg" in line:
                line = line.replace("liveimg", "liveimg overlay=" + usblabel)
                line = line.replace(" ro ", " rw ")
            syslinux.write(line)
        isolinux.close()
        syslinux.close()

    def delete_liveos(self):
        """ Delete the existing LiveOS """
        for path in [self.get_liveos(), os.path.join(self.dest, 'syslinux'),
                     os.path.join(self.dest, 'isolinux')]:
            if os.path.exists(path):
                self.log.info("Deleting " + path)
                try:
                    shutil.rmtree(path)
                except OSError, e:
                    raise LiveUSBError("Unable to remove previous LiveOS: %s" %
                                       str(e))

    def write_log(self):
        """ Write out our subprocess stdout/stderr to a log file """
        out = file('liveusb-creator.log', 'a')
        out.write(self.output.getvalue())
        out.close()

    def existing_liveos(self):
        return os.path.exists(self.get_liveos())

    def get_liveos(self):
        return os.path.join(self.dest + os.path.sep, "LiveOS")

    def existing_overlay(self):
        return os.path.exists(self.get_overlay())

    def get_overlay(self):
        return os.path.join(self.get_liveos(),
                            'overlay-%s-%s' % (self.label, self.uuid or ''))

    def get_release_from_iso(self):
        """ If the ISO is for a known release, return it. """
        isoname = os.path.basename(self.iso)
        for release in releases:
            if os.path.basename(release['url']) == isoname:
                return release

    def _set_drive(self, drive):
        if not self.drives.has_key(drive):
            raise LiveUSBError("Cannot find device %s" % drive)
        self.log.debug("%s selected: %s" % (drive, self.drives[drive]))
        self._drive = drive
        self.uuid = self.drives[drive]['uuid']
        self.fstype = self.drives[drive]['fstype']

    def get_proxies(self):
        """ Return a dictionary of proxy settings """
        return None


class LinuxLiveUSBCreator(LiveUSBCreator):

    bus = None # the dbus.SystemBus
    hal = None # an org.freedesktop.Hal.Manager dbus.Interface

    def detect_removable_drives(self):
        """ Detect all removable USB storage devices using HAL via D-Bus """
        import dbus
        self.drives = {}
        self.bus = dbus.SystemBus()
        hal_obj = self.bus.get_object("org.freedesktop.Hal",
                                      "/org/freedesktop/Hal/Manager")
        self.hal = dbus.Interface(hal_obj, "org.freedesktop.Hal.Manager")

        devices = []
        if self.opts.force:
            devices = self.hal.FindDeviceStringMatch('block.device',
                                                     self.opts.force)
        else:
            devices = self.hal.FindDeviceByCapability("storage")

        for device in devices:
            dev = self._get_device(device)
            if self.opts.force or dev.GetProperty("storage.bus") == "usb" and \
               dev.GetProperty("storage.removable"):
                if dev.GetProperty("block.is_volume"):
                    self._add_device(dev)
                    continue
                else: # iterate over children looking for a volume
                    children = self.hal.FindDeviceStringMatch("info.parent",
                                                              device)
                    for child in children:
                        child = self._get_device(child)
                        if child.GetProperty("block.is_volume"):
                            self._add_device(child)
                            break

        if not len(self.drives):
            raise LiveUSBError("Unable to find any USB drives")

    def _add_device(self, dev):
        mount = str(dev.GetProperty('volume.mount_point'))
        device = str(dev.GetProperty('block.device'))
        self.drives[device] = {
            'label'   : str(dev.GetProperty('volume.label')).replace(' ', '_'),
            'fstype'  : str(dev.GetProperty('volume.fstype')),
            'uuid'    : str(dev.GetProperty('volume.uuid')),
            'mount'   : mount,
            'udi'     : dev,
            'unmount' : False,
            'free'    : mount and self.get_free_bytes(mount) / 1024**2 or None,
            'device'  : device,
        }

    def mount_device(self):
        """ Mount our device with HAL if it is not already mounted """
        self.dest = self.drive['mount']
        if not self.dest:
            if not self.fstype:
                raise LiveUSBError("Filesystem for %s unknown!" % 
                                   self.drive['device'])
            try:
                self.log.debug("Calling %s.Mount('', %s, [], ...)" % (
                               self.drive['udi'], self.fstype))
                self.drive['udi'].Mount('', self.fstype, [],
                        dbus_interface='org.freedesktop.Hal.Device.Volume')
            except Exception, e:
                raise LiveUSBError("Unable to mount device: %s" % str(e))
            device = self.hal.FindDeviceStringMatch('block.device',
                                                    self.drive['device'])
            device = self._get_device(device[0])
            self.dest = device.GetProperty('volume.mount_point')
            self.log.debug("Mounted %s to %s " % (self.drive['device'],
                                                  self.dest))
            self.drive['mount'] = self.dest
            self.drive['unmount'] = True
        else:
            self.log.debug("Using existing mount: %s" % self.dest)

    def unmount_device(self):
        """ Unmount our device if we mounted it to begin with """
        import dbus
        if self.dest and self.drive.get('unmount'):
            self.log.debug("Unmounting %s from %s" % (self.drive['device'],
                                                      self.dest))
            try:
                self.drive['udi'].Unmount([],
                        dbus_interface='org.freedesktop.Hal.Device.Volume')
            except dbus.exceptions.DBusException, e:
                raise
                self.log.warning("Unable to unmount device: %s" % str(e))
                return
            self.drive['unmount'] = False
            self.drive['mount'] = None
            if os.path.exists(self.dest):
                self.log.error("Mount %s exists after unmounting" % self.dest)
                #shutil.rmtree(self.dest) too agressive?
            self.dest = None

    def verify_filesystem(self):
        if self.fstype not in ('vfat', 'msdos', 'ext2', 'ext3'):
            if not self.fstype:
                raise LiveUSBError("Unknown filesystem for %s.  Your device "
                                   "may need to be reformatted.")
            else:
                raise LiveUSBError("Unsupported filesystem: %s" % self.fstype)
        if self.drive['label']:
            self.label = self.drive['label']
        else:
            self.log.info("Setting %s label to %s" % (self.drive['device'],
                                                      self.label))
            try:
                if self.fstype in ('vfat', 'msdos'):
                    # @@ Fix this, it doesn't seem to work...
                    self.popen('/sbin/dosfslabel %s %s' % (self.drive['device'],
                                                           self.label))
                else:
                    self.popen('/sbin/e2label %s %s' % (self.drive['device'],
                                                        self.label))
            except LiveUSBError, e:
                self.log.error("Unable to change volume label: %s" % str(e))
                self.label = None

    def extract_iso(self):
        """ Extract self.iso to self.dest """
        tmpdir = tempfile.mkdtemp()
        self.log.info("Extracting ISO to device")
        self.popen('mount -o loop,ro %s %s' % (self.iso, tmpdir))
        tmpliveos = os.path.join(tmpdir, 'LiveOS')
        if not os.path.isdir(tmpliveos):
            raise LiveUSBError("Unable to find LiveOS on ISO")
        liveos = os.path.join(self.dest, 'LiveOS')
        if not os.path.exists(liveos):
            os.mkdir(liveos)
        for img in ('squashfs.img', 'osmin.img'):
            self.popen('cp %s %s' % (os.path.join(tmpliveos, img),
                                     os.path.join(liveos, img)))
        isolinux = os.path.join(self.dest, 'isolinux')
        if not os.path.exists(isolinux):
            os.mkdir(isolinux)
        self.popen('cp %s/* %s' % (os.path.join(tmpdir, 'isolinux'), isolinux))

    def install_bootloader(self):
        """ Run syslinux to install the bootloader on our devices """
        self.log.info("Installing bootloader")
        shutil.move(os.path.join(self.dest, "isolinux"),
                    os.path.join(self.dest, "syslinux"))
        os.unlink(os.path.join(self.dest, "syslinux", "isolinux.cfg"))
        self.popen('syslinux%s%s -d %s %s' %  (self.opts.force and ' -f' or ' ',
                   self.opts.safe and ' -s' or ' ',
                   os.path.join(self.dest, 'syslinux'), self.drive['device']))

    def get_free_bytes(self, device=None):
        """ Return the number of available bytes on our device """
        import statvfs
        device = device and device or self.dest
        stat = os.statvfs(device)
        return stat[statvfs.F_BSIZE] * stat[statvfs.F_BAVAIL]

    def _get_device(self, udi):
        """ Return a dbus Interface to a specific HAL device UDI """
        import dbus
        dev_obj = self.bus.get_object("org.freedesktop.Hal", udi)
        return dbus.Interface(dev_obj, "org.freedesktop.Hal.Device")

    def terminate(self):
        import signal
        self.log.info("Cleaning up...")
        for pid in self.pids:
            try:
                os.kill(pid, signal.SIGHUP)
                self.log.debug("Killed process %d" % pid)
            except OSError:
                pass
        self.unmount_device()


class WindowsLiveUSBCreator(LiveUSBCreator):

    def detect_removable_drives(self):
        import win32file, win32api
        self.drives = {}
        for drive in [l + ':' for l in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']:
            if win32file.GetDriveType(drive) == win32file.DRIVE_REMOVABLE or \
               drive == self.opts.force:
                try:
                    vol = win32api.GetVolumeInformation(drive)
                    label = vol[0]
                except:
                    label = None
                self.drives[drive] = {
                    'label': label,
                    'mount': drive,
                    'uuid': self._get_device_uuid(drive),
                    'free': self.get_free_bytes(drive) / 1024**2,
                    'fstype': 'vfat',
                    'device': drive,
                }
        if not len(self.drives):
            raise LiveUSBError("Unable to find any removable devices")

    def verify_filesystem(self):
        import win32api, win32file, pywintypes
        try:
            vol = win32api.GetVolumeInformation(self.drive['device'])
        except Exception, e:
            raise LiveUSBError("Make sure your USB key is plugged in and "
                               "formatted with the FAT filesystem")
        if vol[-1] not in ('FAT32', 'FAT'):
            raise LiveUSBError("Unsupported filesystem: %s\nPlease backup and "
                               "format your USB key with the FAT filesystem." %
                               vol[-1])
        self.fstype = 'vfat'
        if vol[0] == '':
            try:
                win32file.SetVolumeLabel(self.drive['device'], self.label)
                self.log.info("Set %s label to %s" % (self.drive['device'],
                                                      self.label))
            except pywintypes.error, e:
                self.log.warning("Unable to SetVolumeLabel: " + str(e))
                self.label = None
        else:
            self.label = vol[0].replace(' ', '_')

    def get_free_bytes(self, device=None):
        """ Return the number of free bytes on our selected drive """
        import win32file
        device = device and device or self.drive['device']
        (spc, bps, fc, tc) = win32file.GetDiskFreeSpace(device)
        return fc * (spc * bps) # free-clusters * bytes per-cluster

    def extract_iso(self):
        """ Extract our ISO with 7-zip directly to the USB key """
        self.log.info("Extracting ISO to USB device")
        self.popen('7z x "%s" -x![BOOT] -y -o%s' % (
                   self.iso, self.drive['device']))

    def install_bootloader(self):
        """ Run syslinux to install the bootloader on our device """
        self.log.info("Installing bootloader")
        device = self.drive['device']
        if os.path.isdir(os.path.join(device + os.path.sep, "syslinux")):
            syslinuxdir = os.path.join(device + os.path.sep, "syslinux")
            # Python for Windows is unable to delete read-only files, and some
            # may exist here if the LiveUSB stick was created in Linux
            for f in os.listdir(syslinuxdir):
                os.chmod(os.path.join(syslinuxdir, f), 0777)
            shutil.rmtree(syslinuxdir)
        shutil.move(os.path.join(device + os.path.sep, "isolinux"),
                    os.path.join(device + os.path.sep, "syslinux"))
        os.unlink(os.path.join(device + os.path.sep, "syslinux",
                               "isolinux.cfg"))
        self.popen('syslinux%s%s -m -a -d %s %s' %  (self.opts.force and ' -f'
                   or ' ', self.opts.safe and ' -s' or ' ',
                   os.path.join(device + os.path.sep, 'syslinux'), device))

    def _get_device_uuid(self, drive):
        """ Return the UUID of our selected drive """
        uuid = None
        try:
            import win32com.client
            uuid = win32com.client.Dispatch("WbemScripting.SWbemLocator") \
                         .ConnectServer(".", "root\cimv2") \
                         .ExecQuery("Select VolumeSerialNumber from "
                                    "Win32_LogicalDisk where Name = '%s'" %
                                    drive)[0].VolumeSerialNumber
            if uuid == 'None':
                uuid = None
            else:
                uuid = uuid[:4] + '-' + uuid[4:]
        except Exception, e:
            self.log.warning("Exception while fetching UUID: %s" % str(e))
            raise
        self.log.debug("Found UUID %s for %s" % (uuid, drive))
        return uuid

    def popen(self, cmd, **kwargs):
        import win32process
        if isinstance(cmd, basestring):
            cmd = cmd.split()
        tool = os.path.join('tools', '%s.exe' % cmd[0])
        if not os.path.exists(tool):
            raise LiveUSBError("Cannot find '%s'.  Make sure to extract the "
                               "entire liveusb-creator zip file before running "
                               "this program.")
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

    def mount_device(self):
        self.dest = self.drive['mount']

    def unmount_device(self):
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
            self.log.warning('Unable to detect proxy settings: %s' % str(e))
        self.log.debug('Using proxies: %s' % proxies)
        return proxies
