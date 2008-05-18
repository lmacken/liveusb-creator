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
    drives = []         # a list of removable devices
    drive = None        # the selected device that we are installing to
    overlay = 0         # size in mb of our persisten overlay
    log = StringIO()    # log subprocess output in case of errors
    uuid = None         # the uuid of our selected drive
    pids = []           # a list of pids of all of our subprocesses

    def detectRemovableDrives(self):
        """ This method should populate self.drives """
        raise NotImplementedError

    def verifyFilesystem(self):
        """
        Verify the filesystem of our device, setting the volume label
        if necessary.  If something is not right, this method throws a
        LiveUSBError.
        """
        raise NotImplementedError

    def installBootloader(self, force=False):
        """ Install the bootloader to our device, using syslinux """
        raise NotImplementedError

    def _getDeviceUUID(self):
        """ Return the UUID of our self.drive """
        raise NotImplementedError

    def updateConfigs(self):
        """ Generate our syslinux.cfg """
        isolinux = file(os.path.join(self.drive,"isolinux","isolinux.cfg"),'r')
        syslinux = file(os.path.join(self.drive,"isolinux","syslinux.cfg"),'w')
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

    def writeLog(self):
        """ Write out our subprocess stdout/stderr to a log file """
        out = file('liveusb-creator.log', 'a')
        out.write(self.log.getvalue())
        out.close()

    def getReleases(self):
        return [release['name'] for release in releases]

    def existingLiveOS(self):
        return os.path.exists(self.getLiveOS())

    def getLiveOS(self):
        return os.path.join(self.drive, "LiveOS")

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
            bytes = 4096
            total = 0
            while bytes:
                data = isofile.read(bytes)
                checksum.update(data)
                bytes = len(data)
                total += bytes
                progress.updateProgress(total / 1024)
            return checksum.hexdigest() == release['sha1']

    def setDrive(self, drive):
        self.drive = drive
        self._getDeviceUUID()

    def setOverlay(self, overlay):
        self.overlay = overlay


class LinuxLiveUSBCreator(LiveUSBCreator):

    def detectRemovableDrives(self):
        import dbus
        self.bus = dbus.SystemBus()
        hal_obj = self.bus.get_object("org.freedesktop.Hal",
                                      "/org/freedesktop/Hal/Manager")
        self.hal = dbus.Interface(hal_obj, "org.freedesktop.Hal.Manager")
        storage_devices = self.hal.FindDeviceByCapability("storage")

        for device in storage_devices:
            dev = self.getDevice(device)
            if dev.GetProperty("storage.bus") == "usb" and \
               dev.GetProperty("storage.removable"):
                if dev.GetProperty("block.is_volume"):
                    self.drives.append(dev.GetProperty("volume.mount_point"))
                    continue
                else: # iterate over children looking for a volume
                    children = self.hal.FindDeviceStringMatch("info.parent",
                                                              device)
                    for child in children:
                        child = self.getDevice(child)
                        if child.GetProperty("block.is_volume"):
                            self.drives.append(
                                    child.GetProperty("volume.mount_point")
                            )
                            break

        if not len(self.drives):
            raise LiveUSBError("Unable to find any USB drives")
        elif len(self.drives) == 1:
            self.drive = self.drives[0]
        else: # prompt the user which drive to use?
            pass

    def getDevice(self, udi):
        import dbus
        dev_obj = self.bus.get_object("org.freedesktop.Hal", udi)
        return dbus.Interface(dev_obj, "org.freedesktop.Hal.Device")

    def verifyFilesystem(self):
        device = self.hal.FindDeviceStringMatch("volume.mount_point",
                                                self.drive)[0]
        device = self.getDevice(device)
        self.fstype = device.GetProperty("volume.fstype")
        if self.fstype not in ('vfat', 'msdos', 'ext2', 'ext3'):
            raise LiveUSBError("Unsupported filesystem: %s" % self.fstype)

    def createPersistentOverlay(self, size=1024):
        overlay = os.path.join(self.drive, 'LiveOS', 'overlay')
        if self.fstype == 'vfat':
            # vfat apparently can't handle sparse files
            ret = subprocess.call(['dd', 'if=/dev/zero', 'of=%s' % overlay,
                                   'count=%d' % size, 'bs=1M'])
        else:
            ret = subprocess.call(['dd', 'if=/dev/null', 'of=%s' % overlay,
                                   'count=1', 'bs=1M', 'seek=%d' % size])
        if ret or not self.existingOverlay():
            raise LiveUSBError("Error while creating persistent overlay")


class WindowsLiveUSBCreator(LiveUSBCreator):

    def detectRemovableDrives(self):
        import win32file, win32api
        self.drives = []
        for drive in [l + ':' for l in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']:
            if win32file.GetDriveType(drive) == win32file.DRIVE_REMOVABLE:
                try:
                    vol = win32api.GetVolumeInformation(drive)
                    label = vol[0]
                except:
                    label = None
                self.drives.append((drive, label))
        if not len(self.drives):
            raise LiveUSBError("Unable to find any removable devices")

    def verifyFilesystem(self):
        import win32api, win32file
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
            win32file.SetVolumeLabel(self.drive, self.label)
        else:
            self.label = vol[0].replace(' ', '_')

    def installBootloader(self, force=False):
        """ Run syslinux to install the bootloader on our devices """
        import win32process
        if os.path.isdir(os.path.join(self.drive, "syslinux")):
            syslinuxdir = os.path.join(self.drive, "syslinux")
            # Python for Windows is unable to delete read-only files, and some
            # may exist here if the LiveUSB stick was created in Linux
            for f in os.listdir(syslinuxdir):
                os.chmod(os.path.join(syslinuxdir, f), 0777)
            shutil.rmtree(os.path.join(self.drive, "syslinux"))
        shutil.move(os.path.join(self.drive, "isolinux"),
                    os.path.join(self.drive, "syslinux"))
        os.unlink(os.path.join(self.drive, "syslinux", "isolinux.cfg"))
        p = subprocess.Popen([os.path.join('tools', 'syslinux.exe'),
                              force and '-f' or '', '-m', '-a', '-d',
                              os.path.join(self.drive, 'syslinux'), self.drive],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             creationflags=win32process.CREATE_NO_WINDOW)
        self.pids.append(p.pid)
        map(self.log.write, p.communicate())
        if p.returncode:
            self.writeLog()
            raise LiveUSBError("An error occured while installing the "
                               "bootloader.  The syslinux output as been "
                               "written to liveusb-creator.log")

    def checkFreeSpace(self):
        """ Make sure there is enough space for the LiveOS and overlay """
        import win32file
        (spc, bps, fc, tc) = win32file.GetDiskFreeSpace(self.drive)
        bpc = spc * bps # bytes-per-cluster
        free_bytes = fc * bpc

        self.isosize = os.stat(self.iso)[ST_SIZE]
        overlaysize = self.overlay * 1024 * 1024
        self.totalsize = overlaysize + self.isosize

        if self.totalsize > free_bytes:
            raise LiveUSBError("Not enough free space on device")

    def extractISO(self):
        """ Extract our ISO with 7-zip directly to the USB key """
        import win32process
        p = subprocess.Popen([os.path.join('tools', '7z.exe'), 'x',
                              self.iso, '-x![BOOT]', '-y', '-o' + self.drive],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             creationflags=win32process.CREATE_NO_WINDOW)
        self.pids.append(p.pid)
        map(self.log.write, p.communicate())
        if p.returncode or not self.existingLiveOS():
            self.writeLog()
            raise LiveUSBError("ISO extraction failed? Cannot find LiveOS")

    def createPersistentOverlay(self):
        if self.overlay:
            import win32process
            p = subprocess.Popen([os.path.join('tools', 'dd.exe'),
                                  'if=/dev/zero', 'of=' + self.getOverlay(),
                                  'count=%d' % self.overlay, 'bs=1M'],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 creationflags=win32process.CREATE_NO_WINDOW)
            self.pids.append(p.pid)
            map(self.log.write, p.communicate())
            if p.returncode or not self.existingOverlay():
                self.writeLog()
                raise LiveUSBError("Persistent overlay creation failed")

    def _getDeviceUUID(self):
        """ Return the UUID of our selected drive """
        if not self.uuid:
            try:
                import win32com.client
                wmi = win32com.client.GetObject("winmgmts:")
                result = wmi.ExecQuery('SELECT VolumeSerialNumber FROM '
                                       'Win32_LogicalDisk WHERE Name="%s"' %
                                       self.drive)
                if result and len(result):
                    uuid = str(result[0].Properties_("VolumeSerialNumber"))
                    if uuid == 'None':
                        self.uuid = None
                    else:
                        self.uuid = uuid[:4] + '-' + uuid[4:]
            except:
                self.uuid = None
        return self.uuid

# vim:ts=4 sw=4 expandtab:
