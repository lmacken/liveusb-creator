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
    pass


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

    # The selected device
    drive = property(fget=lambda self: self._drive,
                     fset=lambda self, d: self._setDrive(d))
    _drive = None

    def __init__(self, opts):
        self.opts = opts
        self.setupLogger()

    def setupLogger(self):
        self.log = logging.getLogger(__name__)
        level = logging.INFO
        if self.opts.verbose:
            level = logging.DEBUG
        self.log.setLevel(level)
        ch = logging.StreamHandler()
        ch.setLevel(level)
        formatter = logging.Formatter("[%(module)s:%(lineno)s] %(message)s")
        ch.setFormatter(formatter)
        self.log.addHandler(ch)

    def detectRemovableDrives(self, force=None):
        """ This method should populate self.drives with removable devices.

        If an optional 'force' argument is given, use the specified device
        regardless of whether it is removable or not.
        """
        raise NotImplementedError

    def verifyFilesystem(self):
        """
        Verify the filesystem of our device, setting the volume label
        if necessary.  If something is not right, this method throws a
        LiveUSBError.
        """
        raise NotImplementedError

    def extractISO(self):
        """ Extract the LiveCD ISO to the USB drive """
        raise NotImplementedError

    def installBootloader(self, force=False, safe=False):
        """ Install the bootloader to our device, using syslinux.

        At this point, we can assume that extractISO has already run, and
        that there is an 'isolinux' directory on our device.
        """
        raise NotImplementedError

    def _getDeviceUUID(self):
        """ Return the UUID of our self.drive """
        raise NotImplementedError

    def terminate(self):
        """ Terminate any subprocesses that we have spawned """
        raise NotImplementedError

    def mountDevice(self):
        """ Mount self.drive, setting the mount point to self.mount """
        raise NotImplementedError

    def unmountDevice(self):
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
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, stdin=subprocess.PIPE,
                             shell=True, **kwargs)
        self.pids.append(p.pid)
        out, err = p.communicate()
        self.output.write(out + '\n' + err + '\n')
        if p.returncode:
            self.writeLog()
            raise LiveUSBError("There was a problem executing the following "
                               "command: `%s`\nA more detailed error log has "
                               "been written to 'liveusb-creator.log'" % cmd)
        return p

    def verifyImage(self, progress=None):
        """ Verify the SHA1 checksum of our ISO if it is in our release list """
        if not progress:
            class DummyProgress:
                def setMaxProgress(self, value): pass
                def updateProgress(self, value): pass
            progress = DummyProgress()
        release = self.getReleaseFromISO()
        if release:
            progress.setMaxProgress(self.isosize / 1024)
            checksum = sha.new()
            isofile = file(self.iso, 'rb')
            bytes = 1024**2
            total = 0
            while bytes:
                data = isofile.read(bytes)
                checksum.update(data)
                bytes = len(data)
                total += bytes
                progress.updateProgress(total / 1024)
            return checksum.hexdigest() == release['sha1']

    def checkFreeSpace(self):
        """ Make sure there is enough space for the LiveOS and overlay """
        freebytes = self.getFreeBytes()
        self.log.debug('freebytes = %d' % freebytes)
        self.isosize = os.stat(self.iso)[ST_SIZE]
        self.log.debug('isosize = %d' % self.isosize)
        overlaysize = self.overlay * 1024**2
        self.log.debug('overlaysize = %d' % overlaysize)
        self.totalsize = overlaysize + self.isosize
        if self.totalsize > freebytes:
            raise LiveUSBError("Not enough free space on device.\n\t"
                               "%dMB ISO + %dMB overlay > %dMB free space" % 
                               (self.isosize/1024**2, self.overlay,
                                freebytes/1024**2))

    def createPersistentOverlay(self):
        if self.overlay:
            self.log.info("Creating %sMB persistent overlay" % self.overlay)
            if self.fstype == 'vfat':
                # vfat apparently can't handle sparse files
                self.popen('dd if=/dev/zero of=%s count=%d bs=1M'
                           % (self.getOverlay(), self.overlay))
            else:
                self.popen('dd if=/dev/zero of=%s count=1 bs=1M seek=%d'
                           % (self.getOverlay(), self.overlay))

    def updateConfigs(self):
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

    def deleteLiveOS(self):
        """ Delete the existing LiveOS """
        for d in [self.getLiveOS(), os.path.join(self.dest, 'syslinux'),
                  os.path.join(self.dest, 'isolinux')]:
            if os.path.exists(d):
                self.log.info("Deleting " + d)
                try:
                    shutil.rmtree(d)
                except OSError, e:
                    raise LiveUSBError("Unable to remove previous LiveOS: %s" %
                                       str(e))

    def writeLog(self):
        """ Write out our subprocess stdout/stderr to a log file """
        out = file('liveusb-creator.log', 'a')
        out.write(self.output.getvalue())
        out.close()

    def getReleases(self):
        return [release['name'] for release in releases]

    def existingLiveOS(self):
        return os.path.exists(self.getLiveOS())

    def getLiveOS(self):
        return os.path.join(self.dest + os.path.sep, "LiveOS")

    def existingOverlay(self):
        return os.path.exists(self.getOverlay())

    def getOverlay(self):
        return os.path.join(self.getLiveOS(),
                            'overlay-%s-%s' % (self.label, self.uuid or ''))

    def getReleaseFromISO(self):
        """ If the ISO is for a known release, return it. """
        isoname = os.path.basename(self.iso)
        for release in releases:
            if os.path.basename(release['url']) == isoname:
                return release

    def _setDrive(self, drive):
        if not self.drives.has_key(drive):
            raise LiveUSBError("Cannot find device %s" % drive)
        self.log.debug("%s selected: %s" % (drive, self.drives[drive]))
        self._drive = drive
        self.uuid = self.drives[drive]['uuid']
        self.fstype = self.drives[drive]['fstype']


class LinuxLiveUSBCreator(LiveUSBCreator):

    def detectRemovableDrives(self, force=None):
        import dbus
        self.drives = {}
        if force:
            self.drives[force] = {'label': None, 'mount': None}
            return
        self.bus = dbus.SystemBus()
        hal_obj = self.bus.get_object("org.freedesktop.Hal",
                                      "/org/freedesktop/Hal/Manager")
        self.hal = dbus.Interface(hal_obj, "org.freedesktop.Hal.Manager")
        storage_devices = self.hal.FindDeviceByCapability("storage")

        for device in storage_devices:
            dev = self._getDevice(device)
            if dev.GetProperty("storage.bus") == "usb" and \
               dev.GetProperty("storage.removable"):
                if dev.GetProperty("block.is_volume"):
                    self._addDevice(dev)
                    continue
                else: # iterate over children looking for a volume
                    children = self.hal.FindDeviceStringMatch("info.parent",
                                                              device)
                    for child in children:
                        child = self._getDevice(child)
                        if child.GetProperty("block.is_volume"):
                            self._addDevice(child)
                            break

        if not len(self.drives):
            raise LiveUSBError("Unable to find any USB drives")

    def _addDevice(self, dev):
        device = str(dev.GetProperty('block.device'))
        self.drives[device] = {
                'label'   : str(dev.GetProperty('volume.label')).replace(' ', '_'),
                'mount'   : str(dev.GetProperty('volume.mount_point')),
                'fstype'  : str(dev.GetProperty('volume.fstype')),
                'uuid'    : str(dev.GetProperty('volume.uuid')),
                'udi'     : dev,
                'unmount' : False,
                'free'    : self.getFreeBytes(device) / 1024**2
        }

    def mountDevice(self):
        """ Mount our device with HAL if it is not already mounted """
        self.dest = self.drives[self.drive]['mount']
        if self.dest in (None, ''):
            self.dest = tempfile.mkdtemp(dir='/media')
            self.log.debug("Mounting %s to %s" % (self.drive, self.dest))
            self.drives[self.drive]['udi'].Mount('', self.fstype, [],
                    dbus_interface='org.freedesktop.Hal.Device.Volume')
            self.drives[self.drive]['unmount'] = True

    def unmountDevice(self):
        """ Unmount our device if we mounted it to begin with """
        import dbus
        if self.dest and self.drives[self.drive].has_key('unmount'):
            self.log.debug("Unmounting %s from %s" % (self.drive, self.dest))
            try:
                self.drives[self.drive]['udi'].Unmount([],
                        dbus_interface='org.freedesktop.Hal.Device.Volume')
            except dbus.exceptions.DBusException, e:
                self.log.warning("Unable to unmount device: %s" % str(e))
                return
            self.drives[self.drive]['unmount'] = False
            if os.path.exists(self.dest):
                shutil.rmtree(self.dest)
            self.dest = None

    def verifyFilesystem(self):
        if self.fstype not in ('vfat', 'msdos', 'ext2', 'ext3'):
            raise LiveUSBError("Unsupported filesystem: %s" % self.fstype)
        if self.drives[self.drive]['label']:
            self.label = self.drives[self.drive]['label']
        else:
            self.log.info("Setting label on %s to %s" % (self.drive,self.label))
            if self.fstype in ('vfat', 'msdos'):
                p = self.popen('/sbin/dosfslabel %s %s' % (self.drive,
                                                           self.label))
            else:
                p = self.popen('/sbin/e2label %s %s' % (self.drive, self.label))
            if p.returncode:
                self.log.warning("Failed to set label")
                self.label = None

    def extractISO(self):
        """ Extract self.iso to self.dest """
        tmpdir = tempfile.mkdtemp()
        self.log.info("Extracting ISO to device")
        self.popen('mount -o loop,ro %s %s' % (self.iso, tmpdir))
        try:
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
            self.popen('cp %s/* %s' % (os.path.join(tmpdir, 'isolinux'),
                                       isolinux))
        finally:
            self.popen('umount ' + tmpdir)

    def installBootloader(self, force=False, safe=False):
        """ Run syslinux to install the bootloader on our devices """
        self.log.info("Installing bootloader")
        shutil.move(os.path.join(self.dest, "isolinux"),
                    os.path.join(self.dest, "syslinux"))
        os.unlink(os.path.join(self.dest, "syslinux", "isolinux.cfg"))
        self.popen('syslinux%s%s -d %s %s' %  (force and ' -f' or ' ',
                   safe and ' -s' or ' ', os.path.join(self.dest, 'syslinux'),
                   self.drive))

    def getFreeBytes(self, device=None):
        """ Return the number of available bytes on our device """
        import statvfs
        device = device and device or self.dest
        stat = os.statvfs(device)
        return stat[statvfs.F_BSIZE] * stat[statvfs.F_BAVAIL]

    def _getDevice(self, udi):
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
        self.unmountDevice()


class WindowsLiveUSBCreator(LiveUSBCreator):

    def detectRemovableDrives(self, force=None):
        import win32file, win32api
        self.drives = {}
        for drive in [l + ':' for l in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']:
            if win32file.GetDriveType(drive) == win32file.DRIVE_REMOVABLE or \
               drive == force:
                try:
                    vol = win32api.GetVolumeInformation(drive)
                    label = vol[0]
                except:
                    label = None
                self.drives[drive] = {'label': label, 'mount': drive,
                                      'uuid': self._getDeviceUUID(drive)}
        if not len(self.drives):
            raise LiveUSBError("Unable to find any removable devices")

    def verifyFilesystem(self, force=False):
        import win32api, win32file, pywintypes
        try:
            vol = win32api.GetVolumeInformation(self.drive)
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
                win32file.SetVolumeLabel(self.drive, self.label)
                self.log.info("Set label on %s to %s" % (self.drive,self.label))
            except pywintypes.error, e:
                self.log.warning("Unable to SetVolumeLabel: " + str(e))
                self.label = None
        else:
            self.label = vol[0].replace(' ', '_')

    def getFreeBytes(self, device=None):
        """ Return the number of free bytes on self.drive """
        import win32file
        device = device and device or self.drive
        (spc, bps, fc, tc) = win32file.GetDiskFreeSpace(device)
        return fc * (spc * bps) # free-clusters * bytes per-cluster

    def extractISO(self):
        """ Extract our ISO with 7-zip directly to the USB key """
        self.log.info("Extracting ISO to USB device")
        self.popen('7z x "%s" -x![BOOT] -y -o%s' % (self.iso, self.drive))

    def installBootloader(self, force=False, safe=False):
        """ Run syslinux to install the bootloader on our devices """
        self.log.info("Installing bootloader")
        if os.path.isdir(os.path.join(self.drive + os.path.sep, "syslinux")):
            syslinuxdir = os.path.join(self.drive + os.path.sep, "syslinux")
            # Python for Windows is unable to delete read-only files, and some
            # may exist here if the LiveUSB stick was created in Linux
            for f in os.listdir(syslinuxdir):
                os.chmod(os.path.join(syslinuxdir, f), 0777)
            shutil.rmtree(syslinuxdir)
        shutil.move(os.path.join(self.drive + os.path.sep, "isolinux"),
                    os.path.join(self.drive + os.path.sep, "syslinux"))
        os.unlink(os.path.join(self.drive + os.path.sep, "syslinux",
                               "isolinux.cfg"))
        self.popen('syslinux%s%s -m -a -d %s %s' %  (force and ' -f' or ' ',
                   safe and ' -s' or ' ',
                   os.path.join(self.drive + os.path.sep, 'syslinux'),
                   self.drive))

    def _getDeviceUUID(self, drive):
        """ Return the UUID of our selected drive """
        uuid = None
        try:
            import win32com.client
            wmi = win32com.client.GetObject("winmgmts:")
            result = wmi.ExecQuery('SELECT VolumeSerialNumber FROM '
                                   'Win32_LogicalDisk WHERE Name="%s"' %
                                   self.drive)
            if result and len(result):
                serial = str(result[0].Properties_("VolumeSerialNumber"))
                if uuid == 'None':
                    uuid = None
                else:
                    uuid = serial[:4] + '-' + serial[4:]
        except Exception, e:
            self.log.warning("Exception while fetching UUID: %s" % str(e))
        return uuid

    def popen(self, cmd):
        import win32process
        if isinstance(cmd, basestring): cmd = cmd.split()
        cmd = [os.path.join('tools', '%s.exe' % cmd[0])] + cmd[1:]
        try:
            return LiveUSBCreator.popen(self, ' '.join(cmd),
                    creationflags=win32process.CREATE_NO_WINDOW)
        except Exception, e:
            self.log.error("Error executing command: %s" % str(e))
            raise LiveUSBError("Unable to execute command.  Make sure that "
                               "you have fully extracted the zip file before "
                               "running this program.")

    def terminate(self):
        """ Terminate any subprocesses that we have spawned """
        import win32api, win32con, pywintypes
        for pid in self.pids:
            try:
                handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE,
                                              False, pid)
                self.log.debug("Terminating process %s" % pid)
                win32api.TerminateProcess(handle, -1)
                win32api.CloseHandle(handle)
            except pywintypes.error:
                pass

    def mountDevice(self):
        self.dest = self.drives[self.drive]['mount']

    def unmountDevice(self):
        pass
