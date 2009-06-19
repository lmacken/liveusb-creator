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
import hashlib
import shutil
import os
import re

from StringIO import StringIO
from datetime import datetime
from stat import ST_SIZE

from liveusb.releases import releases
from liveusb import _


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
    mb_per_sec = 0      # how many megabytes per second we can write
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
        self.handler = logging.StreamHandler()
        self.handler.setLevel(level)
        formatter = logging.Formatter("[%(module)s:%(lineno)s] %(message)s")
        self.handler.setFormatter(formatter)
        self.log.addHandler(self.handler)

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

    def verify_iso_md5(self):
        """ Verify the MD5 checksum of the ISO """
        raise NotImplementedError

    def install_bootloader(self):
        """ Install the bootloader to our device.

        Platform-specific classes inheriting from the LiveUSBCreator are
        expected to implement this method to install the bootloader to the
        specified device using syslinux.  This specific implemention is 
        platform independent and performs sanity checking along with adding
        OLPC support.
        """
        if not os.path.exists(os.path.join(self.dest, 'isolinux')):
            raise LiveUSBError('extract_iso must be run before '
                               'install_bootloader')
        if self.opts.xo:
            self.setup_olpc()

    def setup_olpc(self):
        """ Install the Open Firmware configuration for the OLPC.

        This method will make the selected device bootable on the OLPC.  It
        does this by installing a /boot/olpc.fth open firmware configuration
        file that enables booting off of USB and SD cards on the XO.
        """
        from liveusb.olpc import ofw_config
        self.log.info(_('Setting up OLPC boot file...'))
        args = self.get_kernel_args()
        if not os.path.exists(os.path.join(self.dest, 'boot')):
            os.mkdir(os.path.join(self.dest, 'boot'))
        olpc_cfg = file(os.path.join(self.dest, 'boot', 'olpc.fth'), 'w')
        olpc_cfg.write(ofw_config % ' '.join(args))
        olpc_cfg.close()
        self.log.debug('Wrote %s' % olpc_cfg.name)

    def get_kernel_args(self):
        """ Grab the kernel arguments from our syslinux configuration """
        args = []
        cfg = file(os.path.join(self.dest, 'isolinux', 'syslinux.cfg'))
        for line in cfg.readlines():
            if 'append' in line:
                args.extend([arg for arg in line.split()[1:]
                             if not arg.startswith('initrd')])
                break
        cfg.close()
        return args

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
        self.log.debug(cmd)
        self.output.write(cmd)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, stdin=subprocess.PIPE,
                                shell=True, **kwargs)
        self.pids.append(proc.pid)
        out, err = proc.communicate()
        self.output.write(out + '\n' + err + '\n')
        if proc.returncode:
            self.write_log()
            raise LiveUSBError(_("There was a problem executing the following "
                                 "command: `%s`\nA more detailed error log has "
                                 "been written to 'liveusb-creator.log'" % cmd))
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
                hash = 'sha1'
                checksum = hashlib.sha1()
            elif 'sha256' in release:
                self.log.info(_("Verifying SHA256 checksum of LiveCD image..."))
                hash = 'sha256'
                checksum = hashlib.sha256()
            isofile = file(self.iso, 'rb')
            bytes = 1024**2
            total = 0
            while bytes:
                data = isofile.read(bytes)
                checksum.update(data)
                bytes = len(data)
                total += bytes
                progress.update_progress(total / 1024)
            if checksum.hexdigest() == release[hash]:
                return True
            else:
                self.log.info(_("Error: The SHA1 of your Live CD is "
                                "invalid.  You can run this program with "
                                "the --noverify argument to bypass this "
                                "verification check."))
                return False
        else:
            self.log.debug(_('Unknown ISO, skipping checksum verification'))

    def check_free_space(self):
        """ Make sure there is enough space for the LiveOS and overlay """
        freebytes = self.get_free_bytes()
        self.log.debug('freebytes = %d' % freebytes)
        self.log.debug('isosize = %d' % self.isosize)
        overlaysize = self.overlay * 1024**2
        self.log.debug('overlaysize = %d' % overlaysize)
        self.totalsize = overlaysize + self.isosize
        if self.totalsize > freebytes:
            raise LiveUSBError(_("Not enough free space on device." + 
                                 "\n%dMB ISO + %dMB overlay > %dMB free space" %
                                 (self.isosize/1024**2, self.overlay,
                                  freebytes/1024**2)))

    def create_persistent_overlay(self):
        if self.overlay:
            self.log.info(_("Creating") + " %sMB " % self.overlay +
                          _("persistent overlay"))
            if self.fstype == 'vfat':
                # vfat apparently can't handle sparse files
                self.popen('dd if=/dev/zero of="%s" count=%d bs=1M'
                           % (self.get_overlay(), self.overlay))
            else:
                self.popen('dd if=/dev/zero of="%s" count=1 bs=1M seek=%d'
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
            if self.opts.kernel_args:
                line = line.replace("liveimg", "liveimg %s" %
                                    ' '.join(self.opts.kernel_args.split(',')))
            syslinux.write(line)
        isolinux.close()
        syslinux.close()

    def delete_liveos(self):
        """ Delete the existing LiveOS """
        self.log.info(_('Removing existing Live OS'))
        for path in [self.get_liveos(),
                     os.path.join(self.dest + os.path.sep, 'syslinux'),
                     os.path.join(self.dest + os.path.sep, 'isolinux')]:
            if os.path.exists(path):
                self.log.debug("Deleting " + path)
                try:
                    shutil.rmtree(path)
                except OSError, e:
                    raise LiveUSBError(_("Unable to remove previous LiveOS: "
                                         "%s" % str(e)))

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
            raise LiveUSBError(_("Cannot find device %s" % drive))
        self.log.debug("%s selected: %s" % (drive, self.drives[drive]))
        self._drive = drive
        self.uuid = self.drives[drive]['uuid']
        self.fstype = self.drives[drive]['fstype']

    def get_proxies(self):
        """ Return a dictionary of proxy settings """
        return None

    def get_mbr(self):
        parent = str(self.drive.get('parent', self._drive))
        self.log.debug('Checking the MBR of %s' % parent)
        drive = open(parent, 'rb')
        mbr = ''.join(['%02X' % ord(x) for x in drive.read(2)])
        drive.close()
        self.log.debug('mbr = %r' % mbr)
        return mbr

    def blank_mbr(self):
        """ Return whether the MBR is empty or not """
        return self.get_mbr() == '0000'

    def _get_mbr_bin(self):
        mbr = None
        for mbr_bin in ('/usr/lib/syslinux/mbr.bin',
                        '/usr/share/syslinux/mbr.bin'):
            if os.path.exists(mbr_bin):
                mbr = mbr_bin
        return mbr

    def mbr_matches_syslinux_bin(self):
        """
        Return whether or not the MBR on the drive matches the system's
        syslinux mbr.bin
        """
        mbr_bin = open(self._get_mbr_bin(), 'rb')
        mbr = ''.join(['%02X' % ord(x) for x in mbr_bin.read(2)])
        return mbr == self.get_mbr()

    def reset_mbr(self):
        parent = str(self.drive.get('parent', self._drive))
        if '/dev/loop' not in self.drive:
            self.log.info(_('Resetting Master Boot Record') + ' of %s' % parent)
            mbr = self._get_mbr_bin()
            self.popen('cat %s > %s' % (mbr, parent))
        else:
            self.log.info(_('Drive is a loopback, skipping MBR reset'))

    def bootable_partition(self):
        """ Ensure that the selected partition is flagged as bootable """
        pass

    def set_iso(self, iso):
        """ Select the given ISO """
        self.iso = self._to_unicode(iso)
        self.isosize = os.stat(self.iso)[ST_SIZE]

    def _to_unicode(self, obj, encoding='utf-8'):
        if hasattr(obj, 'toUtf8'): # PyQt4.QtCore.QString
            obj = str(obj.toUtf8())
        if isinstance(obj, basestring):
            if not isinstance(obj, unicode):
                obj = unicode(obj, encoding, 'replace')
        return obj


class LinuxLiveUSBCreator(LiveUSBCreator):

    bus = None # the dbus.SystemBus
    hal = None # the org.freedesktop.Hal.Manager dbus.Interface

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
            if self.opts.force or dev.GetProperty("storage.bus") == "usb":
                if dev.GetProperty("block.is_volume"):
                    self._add_device(dev)
                    continue
                else: # iterate over children looking for a volume
                    children = self.hal.FindDeviceStringMatch("info.parent",
                                                              device)
                    for child in children:
                        child = self._get_device(child)
                        if child.GetProperty("block.is_volume"):
                            self._add_device(child, parent=dev)
                            #break      # don't break, allow all partitions

        if not len(self.drives):
            raise LiveUSBError(_("Unable to find any USB drives"))

    def _add_device(self, dev, parent=None):
        mount = str(dev.GetProperty('volume.mount_point'))
        device = str(dev.GetProperty('block.device'))
        self.drives[device] = {
            'label'   : str(dev.GetProperty('volume.label')).replace(' ', '_'),
            'fstype'  : str(dev.GetProperty('volume.fstype')),
            'fsversion': str(dev.GetProperty('volume.fsversion')),
            'uuid'    : str(dev.GetProperty('volume.uuid')),
            'mount'   : mount,
            'udi'     : dev,
            'unmount' : False,
            'free'    : mount and self.get_free_bytes(mount) / 1024**2 or None,
            'device'  : device,
            'parent'  : parent.GetProperty('block.device')
        }

    def mount_device(self):
        """ Mount our device with HAL if it is not already mounted """
        import dbus
        self.dest = self.drive['mount']
        if not self.dest:
            if not self.fstype:
                raise LiveUSBError(_("Filesystem for %s unknown!" % 
                                     self.drive['device']))
            try:
                self.log.debug("Calling %s.Mount('', %s, [], ...)" % (
                               self.drive['udi'], self.fstype))
                self.drive['udi'].Mount('', self.fstype, [],
                        dbus_interface='org.freedesktop.Hal.Device.Volume')
                self.drive['unmount'] = True
            except dbus.exceptions.DBusException, e:
                if e.get_dbus_name() == \
                        'org.freedesktop.Hal.Device.Volume.AlreadyMounted':
                    self.log.debug('Device already mounted')
            except Exception, e:
                raise LiveUSBError(_("Unable to mount device: %s" % str(e)))
            device = self.hal.FindDeviceStringMatch('block.device',
                                                    self.drive['device'])
            device = self._get_device(device[0])
            self.dest = device.GetProperty('volume.mount_point')
            self.log.debug("Mounted %s to %s " % (self.drive['device'],
                                                  self.dest))
            self.drive['mount'] = self.dest
            self.drive['free'] = self.get_free_bytes(self.dest) / 1024**2
        else:
            self.log.debug("Using existing mount: %s" % self.dest)

    def unmount_device(self, force=False):
        """ Unmount our device """
        import dbus
        #try:
        #    unmount = self.drive.get('unmount', None)
        #except KeyError, e:
        #    self.log.exception(e)
        #    return
        if self.dest or force or (self.drive and
                self.drive.get('unmount', False)):
            self.log.debug("Unmounting %s from %s" % (self.drive['device'],
                                                      self.dest))
            try:
                self.drive['udi'].Unmount([],
                        dbus_interface='org.freedesktop.Hal.Device.Volume')
            except dbus.exceptions.DBusException, e:
                if e.get_dbus_name() == \
                        'org.freedesktop.Hal.Device.Volume.NotMountedByHal':
                    self.log.debug('Device not mounted by HAL; trying manually')
                    self.popen('umount %s' % self.drive['device'])
                else:
                    import traceback
                    self.log.warning("Unable to unmount device: %s" % str(e))
                    self.log.debug(traceback.format_exc())
                    return
            self.drive['unmount'] = False
            self.drive['mount'] = None
            if os.path.exists(self.dest):
                self.log.error("Mount %s exists after unmounting" % self.dest)
            self.dest = None
        else:
            self.log.warning("self.dest and unmount not set, skipping unmount")

    def verify_filesystem(self):
        self.log.info(_("Verifying filesystem..."))
        if self.fstype not in ('vfat', 'msdos', 'ext2', 'ext3'):
            if not self.fstype:
                raise LiveUSBError(_("Unknown filesystem for %s.  Your device "
                                     "may need to be reformatted."))
            else:
                raise LiveUSBError(_("Unsupported filesystem: %s" %
                                     self.fstype))
        if self.drive['label']:
            self.label = self.drive['label']
        else:
            self.log.info("Setting %s label to %s" % (self.drive['device'],
                                                      self.label))
            try:
                if self.fstype in ('vfat', 'msdos'):
                    try:
                        self.popen('/sbin/dosfslabel %s %s' % (
                                   self.drive['device'], self.label))
                    except LiveUSBError:
                        # dosfslabel returns an error code even upon success
                        pass
                else:
                    self.popen('/sbin/e2label %s %s' % (self.drive['device'],
                                                        self.label))
            except LiveUSBError, e:
                self.log.error("Unable to change volume label: %s" % str(e))
                self.label = None

        # Ensure our master boot record is not empty
        if self.blank_mbr():
            self.log.debug(_('Your MBR appears to be blank'))
            # @@ FIXME:  To do this properly, we first need to unmount the
            # device, then reset the mbr, then remount.  However, for some
            # reason we are unable to re-mount the drive after resetting the
            # MBR, and it tends to hose the USB stick as well.  Maybe we need
            # to rescan/reprobe
            # the device with DBus/Hal? -luke
            #    self.live.reset_mbr()

    def extract_iso(self):
        """ Extract self.iso to self.dest """
        self.log.info(_("Extracting live image to USB device..."))
        tmpdir = tempfile.mkdtemp()
        self.popen('mount -o loop,ro "%s" %s' % (self.iso, tmpdir))
        tmpliveos = os.path.join(tmpdir, 'LiveOS')
        try:
            if not os.path.isdir(tmpliveos):
                raise LiveUSBError(_("Unable to find LiveOS on ISO"))
            liveos = os.path.join(self.dest, 'LiveOS')
            if not os.path.exists(liveos):
                os.mkdir(liveos)
            for img in ('squashfs.img', 'osmin.img'):
                start = datetime.now()
                self.popen("cp %s '%s'" % (os.path.join(tmpliveos, img),
                                           os.path.join(liveos, img)))
                delta = datetime.now() - start
                if delta.seconds:
                    self.mb_per_sec = (self.isosize / delta.seconds) / 1024**2
                    if self.mb_per_sec:
                        self.log.info(_("Wrote to device at") + " %d MB/sec" %
                                      self.mb_per_sec)
            isolinux = os.path.join(self.dest, 'isolinux')
            if not os.path.exists(isolinux):
                os.mkdir(isolinux)
            self.popen("cp %s/* '%s'" % (os.path.join(tmpdir, 'isolinux'),
                                       isolinux))
        finally:
            self.popen('umount %s' % tmpdir)

    def install_bootloader(self):
        """ Run syslinux to install the bootloader on our devices """
        LiveUSBCreator.install_bootloader(self)
        self.log.info(_("Installing bootloader..."))
        syslinux_path = os.path.join(self.dest, "syslinux")
        shutil.move(os.path.join(self.dest, "isolinux"), syslinux_path)
        os.unlink(os.path.join(syslinux_path, "isolinux.cfg"))

        # Syslinux doesn't guarantee the API for its com32 modules (#492370)
        for com32mod in ('vesamenu.c32', 'menu.c32'):
            copied = False
            for path in ('/usr/share', '/usr/lib'):
                com32path = os.path.join(path, 'syslinux', com32mod)
                if os.path.isfile(com32path):
                    self.log.debug('Copying %s on to stick' % com32path)
                    shutil.copyfile(com32path, os.path.join(syslinux_path, com32mod))
                    copied = True
                    break
            if copied:
                break

        # Don't prompt about overwriting files from mtools (#491234)
        for ldlinux in [os.path.join(self.dest, p, 'ldlinux.sys')
                        for p in ('syslinux', '')]:
            self.log.debug('Looking for %s' % ldlinux)
            if os.path.isfile(ldlinux):
                self.log.debug(_("Removing") + " %s" % ldlinux)
                os.unlink(ldlinux)

        if self.drive['fstype'] in ('ext2', 'ext3'):
            shutil.move(os.path.join(syslinux_path, "syslinux.cfg"),
                        os.path.join(syslinux_path, "extlinux.conf"))
            self.popen('extlinux -i %s' % syslinux_path)
        else: # FAT
            self.popen('syslinux%s%s -d %s %s' %  (self.opts.force and
                       ' -f' or '', self.opts.safe and ' -s' or '',
                       'syslinux', self.drive['device']))

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
        for pid in self.pids:
            try:
                os.kill(pid, signal.SIGHUP)
                self.log.debug("Killed process %d" % pid)
            except OSError:
                pass
        #self.unmount_device()

    def verify_iso_md5(self):
        """ Verify the ISO md5sum.

        At the moment this is Linux specific, until we port checkisomd5 
        to Windows.
        """
        self.log.info(_('Verifying ISO MD5 checksum'))
        try:
            self.popen('checkisomd5 "%s"' % self.iso)
        except LiveUSBError, e:
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
            from PyQt4 import QtCore
        except ImportError:
            self.log.warning("PyQt4 module not installed; skipping KDE "
                             "proxy detection")
            return
        kioslaverc = QtCore.QDir.homePath() + '/.kde/share/config/kioslaverc'
        if not QtCore.QFile.exists(kioslaverc):
            return {}
        settings = QtCore.QSettings(kioslaverc, QtCore.QSettings.IniFormat)
        settings.beginGroup('Proxy Settings')
        proxies = {}
        # check for KProtocolManager::ManualProxy (the only one we support)
        if settings.value('ProxyType').toInt()[0] == 1:
            httpProxy = settings.value('httpProxy').toString()
            if httpProxy != '':
                proxies['http'] = httpProxy
            ftpProxy = settings.value('ftpProxy').toString()
            if ftpProxy != '':
                proxies['ftp'] = ftpProxy
        return proxies

    def bootable_partition(self):
        """ Ensure that the selected partition is flagged as bootable """
        import parted
        disk, partition = self.get_disk_partition()
        if partition.isFlagAvailable(parted.PARTITION_BOOT):
            if partition.getFlag(parted.PARTITION_BOOT):
                self.log.debug('%s already bootable' % self._drive)
            else:
                partition.setFlag(parted.PARTITION_BOOT)
                disk.commit()
                self.log.info('Marked %s as bootable' % self._drive)
        else:
            self.log.warning('%s does not have boot flag' % self._drive)

    def get_disk_partition(self):
        """ Return the PedDisk and partition of the selected device """
        import parted
        parent = self.drives[self._drive]['parent']
        dev = parted.Device(path = parent)
        disk = parted.Disk(device = dev)
        for part in disk.partitions:
            if self._drive == "/dev/%s" %(part.getDeviceNodeName(),):
                return disk, part
        raise LiveUSBError(_("Unable to find partition"))

    def initialize_zip_geometry(self):
        """ This method initializes the selected device in a zip-like fashion.

        :Note: This feature is currently experimental, and will DESTROY ALL DATA
               on your device!

        More details on this can be found here:
            http://syslinux.zytor.com/doc/usbkey.txt
        """
        #from parted import PedDevice
        self.log.info('Initializing %s in a zip-like fashon' % self._drive)
        heads = 64
        cylinders = 32
        # Is this part even necessary?
        #device = PedDevice.get(self._drive[:-1])
        #cylinders = int(device.cylinders / (64 * 32))
        self.popen('/usr/lib/syslinux/mkdiskimage -4 %s 0 %d %d' % (
                   self._drive[:-1], heads, cylinders))

    def format_device(self):
        """ Format the selected partition as FAT32 """
        self.log.info('Formatting %s as FAT32' % self._drive)
        self.popen('mkfs.vfat -F 32 %s' % self._drive)


class WindowsLiveUSBCreator(LiveUSBCreator):

    def detect_removable_drives(self):
        import win32file, win32api, pywintypes
        self.drives = {}
        for drive in [l + ':' for l in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']:
            if win32file.GetDriveType(drive) == win32file.DRIVE_REMOVABLE or \
               drive == self.opts.force:
                vol = [None]
                try:
                    vol = win32api.GetVolumeInformation(drive)
                except pywintypes.error, e:
                    self.log.error('Unable to get GetVolumeInformation(%s): %s' % (drive, str(e)))
                    continue
                self.drives[drive] = {
                    'label': vol[0],
                    'mount': drive,
                    'uuid': self._get_device_uuid(drive),
                    'free': self.get_free_bytes(drive) / 1024**2,
                    'fstype': 'vfat',
                    'device': drive,
                    'fsversion': vol[-1],
                }
        if not len(self.drives):
            raise LiveUSBError(_("Unable to find any removable devices"))

    def verify_filesystem(self):
        import win32api, win32file, pywintypes
        self.log.info(_("Verifying filesystem..."))
        try:
            vol = win32api.GetVolumeInformation(self.drive['device'])
        except Exception, e:
            raise LiveUSBError(_("Make sure your USB key is plugged in and "
                                 "formatted with the FAT filesystem"))
        if vol[-1] not in ('FAT32', 'FAT'):
            raise LiveUSBError(_("Unsupported filesystem: %s\nPlease backup "
                                 "and format your USB key with the FAT "
                                 "filesystem." % vol[-1]))
        self.fstype = 'vfat'
        if vol[0] == '':
            try:
                win32file.SetVolumeLabel(self.drive['device'], self.label)
                self.log.debug("Set %s label to %s" % (self.drive['device'],
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
        try:
            (spc, bps, fc, tc) = win32file.GetDiskFreeSpace(device)
        except Exception, e:
            self.log.error("Problem determining free space: %s" % str(e))
            return 0
        return fc * (spc * bps) # free-clusters * bytes per-cluster

    def extract_iso(self):
        """ Extract our ISO with 7-zip directly to the USB key """
        self.log.info(_("Extracting live image to USB device..."))
        start = datetime.now()
        self.popen('7z x "%s" -x![BOOT] -y -o%s' % (
                   self.iso, self.drive['device']))
        delta = datetime.now() - start
        if delta.seconds:
            self.mb_per_sec = (self.isosize / delta.seconds) / 1024**2
            if self.mb_per_sec:
                self.log.info(_("Wrote to device at") + " %d MB/sec" % 
                              self.mb_per_sec)

    def install_bootloader(self):
        """ Run syslinux to install the bootloader on our device """
        LiveUSBCreator.install_bootloader(self)
        self.log.info(_("Installing bootloader"))
        device = self.drive['device']
        syslinuxdir = os.path.join(device + os.path.sep, "syslinux")
        if os.path.isdir(syslinuxdir):
            # Python for Windows is unable to delete read-only files, and some
            # may exist here if the LiveUSB stick was created in Linux
            for f in os.listdir(syslinuxdir):
                os.chmod(os.path.join(syslinuxdir, f), 0777)
            shutil.rmtree(syslinuxdir)
        shutil.move(os.path.join(device + os.path.sep, "isolinux"), syslinuxdir)
        os.unlink(os.path.join(syslinuxdir, "isolinux.cfg"))

        # Don't prompt about overwriting files from mtools (#491234)
        for ldlinux in [os.path.join(device + os.path.sep, p, 'ldlinux.sys')
                        for p in (syslinuxdir, '')]:
            if os.path.isfile(ldlinux):
                self.log.debug(_("Removing") + " %s" % ldlinux)
                os.unlink(ldlinux)

        self.popen('syslinux%s%s -m -a -d %s %s' %  (self.opts.force and ' -f'
                   or '', self.opts.safe and ' -s' or '', 'syslinux', device))

    def _get_device_uuid(self, drive):
        """ Return the UUID of our selected drive """
        if self.uuid:
            return self.uuid
        uuid = None
        try:
            import win32com.client
            uuid = win32com.client.Dispatch("WbemScripting.SWbemLocator") \
                         .ConnectServer(".", "root\cimv2") \
                         .ExecQuery("Select VolumeSerialNumber from "
                                    "Win32_LogicalDisk where Name = '%s'" %
                                    drive)[0].VolumeSerialNumber
            if uuid in (None, 'None', ''):
                uuid = None
            else:
                uuid = uuid[:4] + '-' + uuid[4:]
            self.log.debug("Found UUID %s for %s" % (uuid, drive))
        except Exception, e:
            self.log.exception(e)
            self.log.warning("Exception while fetching UUID: %s" % str(e))
        return uuid

    def popen(self, cmd, **kwargs):
        import win32process
        if isinstance(cmd, basestring):
            cmd = cmd.split()
        tool = os.path.join('tools', '%s.exe' % cmd[0])
        if not os.path.exists(tool):
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

    def verify_iso_md5(self):
        """ Verify the ISO md5sum.

        At the moment this is Linux-only, until we port checkisomd5 to Windows.
        """
        return True
