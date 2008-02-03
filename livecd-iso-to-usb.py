# This tool installs a Fedora Live ISO (F7+) on to a USB stick, from Windows.
# For information regarding the installation of Fedora on USB drives, see
# the wiki: http://fedoraproject.org/wiki/FedoraLiveCD/USBHowTo
#
# Copyright 2008  Red Hat, Inc.
# Authors: Luke Macken <lmacken@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import win32file
import win32api
import shutil
import os
import re

class LiveUSBCreator:

    drive = None # F:\
    label = None # FEDORA
    iso   = None # Fedora-8-Live-i686.iso

    def detectRemovableDrives(self):
        """
        Detect all removable drives.  If we find more than one, ask the user
        which they would like to use.
        """
        drives = []
        for drive in [l.upper() + ':' for l in 'abcdefghijklmnopqrstuvwxyz']:
            if win32file.GetDriveType(drive) == win32file.DRIVE_REMOVABLE:
                drives.append(drive)
        if not len(drives):
            raise Exception("Sorry, I couldn't find any devices")
        elif len(drives) > 1:
            drives[0] = raw_input("Which drive do you want to put Fedora on: "
                                  "%s ? " % drives)
            drives[0] = drives[0].upper()
            if not drives[0].endswith(":"):
                drives[0] += ":"
        self.drive = drives[0] + os.sep

    def verifyFilesystem(self):
        """
        Verify our filesystem type, and set the volume label if necessary
        """
        self.label = "FEDORA"
        vol = win32api.GetVolumeInformation(self.drive[:-1])
        if vol[-1] not in ('FAT32', 'FAT'):
            raise Exception("Unsupported filesystem: %s\nPlease backup and "
                            "format your USB key as FAT 16 or 32." % vol[-1])
        if vol[0] == '':
            win32file.SetVolumeLabel(self.drive[:-1], self.label)
        else:
            self.label = vol[0]

    def findISO(self):
        """
        Look in the current directory for our ISO image.
        """
        isos = [item for item in os.listdir(".") if item.endswith(".iso")]
        if not len(isos):
            raise Exception("Cannot find ISO file.  Please drag it into this "
                            "directory.  If you haven't downloaded Fedora yet, "
                            "please visit: http://fedoraproject.org/get-fedora")
        if len(isos) > 1:
            print "I found the following ISOs:"
            for i, iso in enumerate(isos):
                print " [ %d ] %s" % (i + 1, iso)
            choice = raw_input("Which image do you want use: %s ? " %
                               range(1, i + 2))
            isos[0] = isos[int(choice) - 1]
        self.iso = isos[0]

    def extractISO(self):
        """ Extract our ISO with 7-zip directly to the USB key """
        if os.path.isdir(os.path.join(self.drive, "LiveOS")):
            print "Your device already contains a LiveOS!"
        os.system("7-Zip%s7z.exe x %s -x![BOOT] -o%s" % (os.sep, self.iso,
                                                         self.drive))
        if not os.path.isdir(os.path.join(self.drive, "LiveOS")):
            raise Exception("ISO extraction failed? Cannot find LiveOS")

    def updateConfigs(self):
        """ Generate our syslinux.cfg """
        isolinux = file(os.path.join(self.drive,"isolinux","isolinux.cfg"),'r')
        syslinux = file(os.path.join(self.drive,"isolinux","syslinux.cfg"),'w')
        for line in isolinux.readlines():
            if "CDLABEL" in line:
                line = re.sub("CDLABEL=[^ ]*", "LABEL=" + self.label, line)
                line = re.sub("rootfstype=[^ ]*", "rootfstype=vfat", line)
            syslinux.write(line)
        isolinux.close()
        syslinux.close()

    def installBootloader(self):
        print "Installing bootloader"
        shutil.move(os.path.join(self.drive, "isolinux"),
                    os.path.join(self.drive, "syslinux"))
        os.unlink(os.path.join(self.drive, "syslinux", "isolinux.cfg"))
        os.system("syslinux -d %s %s" % (os.path.join(self.drive, "syslinux"),
                                         self.drive[:-1]))

if __name__ == '__main__':
    try:
        live = LiveUSBCreator()
        live.detectRemovableDrives()
        live.verifyFilesystem()
        live.findISO()
        live.extractISO()
        live.updateConfigs()
        live.installBootloader()
    except Exception, e:
        print "Oops!  Something went wrong:"
        print str(e)

    x = raw_input("\nDone!")
