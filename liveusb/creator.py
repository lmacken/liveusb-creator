# -*- coding: utf-8 -*-
#
# This tool installs a Fedora Live ISO (F7+) on to a USB stick, from Windows.
# For information regarding the installation of Fedora on USB drives, see
# the wiki: http://fedoraproject.org/wiki/FedoraLiveCD/USBHowTo
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
import os
import re

from StringIO import StringIO
from stat import ST_SIZE


class LiveUSBCreator(object):
    """ An OS-independent parent class for Live USB Creators """

    iso = None        # the path to our live image
    label = "FEDORA"  # if one doesn't already exist
    fstype = None     # the format of our usb stick
    drives = []       # a list of removable devices
    overlay = 0       # size in mb of our persisten overlay
    log = StringIO()  # log subprocess output in case of errors

    def detectRemovableDrives(self):
        """ This method should populate self.drives """
        raise NotImplementedError

    def verifyFilesystem(self):
        """
        Verify the filesystem of our device, setting the volume label
        if necessary.  If something is not right, this method throws an
        Exception
        """
        raise NotImplementedError

    def updateConfigs(self):
        """ Generate our syslinux.cfg """
        isolinux = file(os.path.join(self.drive,"isolinux","isolinux.cfg"),'r')
        syslinux = file(os.path.join(self.drive,"isolinux","syslinux.cfg"),'w')
        for line in isolinux.readlines():
            if "CDLABEL" in line:
                line = re.sub("CDLABEL=[^ ]*", "LABEL=" + self.label, line)
                line = re.sub("rootfstype=[^ ]*",
                              "rootfstype=%s" % self.fstype,
                              line)
            if self.overlay and "liveimg" in line:
                line = line.replace("liveimg", "liveimg overlay=" + self.label)
                line = line.replace(" ro ", " rw ")
            syslinux.write(line)
        isolinux.close()
        syslinux.close()

    def installBootloader(self):
        """ Run syslinux to install the bootloader on our devices """
        if os.path.isdir(os.path.join(self.drive, "syslinux")):
            shutil.rmtree(os.path.join(self.drive, "syslinux"))
        shutil.move(os.path.join(self.drive, "isolinux"),
                    os.path.join(self.drive, "syslinux"))
        os.unlink(os.path.join(self.drive, "syslinux", "isolinux.cfg"))
        os.system("syslinux -d %s %s" % (os.path.join(self.drive, "syslinux"),
                                         self.drive[:-1]))


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
            raise Exception("Sorry, I can't find any USB drives")

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
            raise Exception("Unsupported filesystem: %s" % self.fstype)
        # TODO: check MBR, isomd5sum, active partition

    def createPersistentOverlay(self, size=1024):
        overlay = os.path.join(self.drive, 'LiveOS', 'overlay')
        if self.fstype == 'vfat':
            # vfat apparently can't handle sparse files
            ret = subprocess.call(['dd', 'if=/dev/zero', 'of=%s' % overlay,
                                   'count=%d' % size, 'bs=1M'])
        else:
            ret = subprocess.call(['dd', 'if=/dev/null', 'of=%s' % overlay,
                                   'count=1', 'bs=1M', 'seek=%d' % size])
        if ret:
            raise Exception("Error while creating persistent overlay")


class WindowsLiveUSBCreator(LiveUSBCreator):

    def detectRemovableDrives(self):
        import win32file
        for drive in [l + ':' for l in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']:
            if win32file.GetDriveType(drive) == win32file.DRIVE_REMOVABLE:
                self.drives.append(drive + os.sep)
        if not len(self.drives):
            raise Exception("Sorry, I couldn't find any devices")

    def verifyFilesystem(self):
        import win32api, win32file
        try:
            vol = win32api.GetVolumeInformation(self.drive[:-1])
        except:
            raise Exception("Make sure your USB key is plugged in and formatted"
                            " using the FAT filesystem" + self.drive)
        if vol[-1] not in ('FAT32', 'FAT'):
            raise Exception("Unsupported filesystem: %s\nPlease backup and "
                            "format your USB key with the FAT filesystem." %
                            vol[-1])
        self.fstype = 'vfat'
        if vol[0] == '':
            win32file.SetVolumeLabel(self.drive[:-1], self.label)
        else:
            self.label = vol[0]

    def extractISO(self):
        """ Extract our ISO with 7-zip directly to the USB key """
        if os.path.isdir(os.path.join(self.drive, "LiveOS")):
            print "Your device already contains a LiveOS!"
        os.system("7-Zip%s7z.exe x %s -x![BOOT] -o%s" % (os.sep, self.iso,
                                                         self.drive))
        if not os.path.isdir(os.path.join(self.drive, "LiveOS")):
            raise Exception("ISO extraction failed? Cannot find LiveOS")

    def createPersistentOverlay(self):
        if self.overlay:
            import win32process
            overlay = os.path.join(self.drive, 'LiveOS', 'overlay')
            p = subprocess.Popen(['dd.exe', 'if=/dev/zero', 'of=' + overlay,
                                  'count=%d' % self.overlay, 'bs=1M'],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 creationflags=win32process.CREATE_NO_WINDOW)
            map(self.log.write, p.communicate())
            if p.returncode:
                self.writeLog()
                raise Exception("Persistent overlay creation failed")

# vim:ts=4 sw=4 expandtab:
