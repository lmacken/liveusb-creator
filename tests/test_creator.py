import os

class LiveUSBCreatorOptions(object):
    console = True
    force = False
    safe = False
    noverify = False
    verbose = False


class TestLiveUSBCreator:

    def _get_creator(self):
        from liveusb import LiveUSBCreator
        opts = LiveUSBCreatorOptions()
        return LiveUSBCreator(opts)

    def test_creation(self):
        from liveusb import LiveUSBCreator
        live = self._get_creator()
        assert live and isinstance(live, LiveUSBCreator)

    def test_device_detection(self):
        live = self._get_creator()
        live.detect_removable_drives()
        assert len(live.drives), "No devices found"
        for drive in live.drives:
            for key in ('label', 'fstype', 'uuid', 'free'):
                assert key in live.drives[drive]

    def test_releases(self):
        from liveusb.releases import releases
        assert releases and len(releases)
        for release in releases:
            assert release['name']
            assert release['url']
            if 'sha1' in release:
                assert len(release['sha1']) == 40
            elif 'sha256' in release:
                assert len(release['sha256']) == 64

    def test_mount_device(self):
        live = self._get_creator()
        live.detect_removable_drives()
        for drive in live.drives:
            live.drive = drive
            if live.drive['mount']:
                assert not live.drive['unmount']
                assert os.path.exists(live.drive['mount'])
                # this method will only unmount if we have mounted it first
                live.unmount_device()
                assert os.path.exists(live.drive['mount'])
                # fake it out, forcing it to unmount
                live.dest = live.drive['mount']
                live.drive['unmount'] = True
                live.unmount_device()
                assert not live.drive['mount'] and not live.drive['unmount']
            live.mount_device()
            assert live.drive['mount'] # make sure we set the mountpoint
            assert live.drive['unmount'] # make sure we know to unmount this
            assert os.path.exists(live.drive['mount']), live.drive

    def test_unmount_device(self):
        live = self._get_creator()
        live.detect_removable_drives()
        for drive in live.drives:
            live.drive = drive
            if live.drive['mount']:
                assert os.path.exists(live.drive['mount'])
                # this method will only unmount if we have mounted it first
                live.unmount_device()
                assert os.path.exists(live.drive['mount'])
                # fake it out, forcing it to unmount
                live.dest = live.drive['mount']
                live.drive['unmount'] = True
                live.unmount_device()
                assert not live.drive['mount'] and not live.drive['unmount']
            else:
                raise Exception, "Device not mounted from previous test?"

    def test_verify_filesystem(self):
        live = self._get_creator()
        live.detect_removable_drives()
        for drive in live.drives:
            live.drive = drive
            assert live.fstype
            live.verify_filesystem()
            assert live.label
            assert live.drive['label']

    def test_extract_iso(self):
        from glob import glob
        live = self._get_creator()
        live.detect_removable_drives()
        isos = filter(lambda x: x.endswith('.iso'), 
                      filter(os.path.isfile, glob('*') + glob('*/*')))
        assert isos, "No ISOs found.  Put one in this directory"
        for drive in live.drives:
            live.drive = drive
            live.iso = isos[0]
            live.mount_device()
            if os.path.exists(live.get_liveos()):
                live.delete_liveos()
            assert not os.path.exists(live.get_liveos())
            live.extract_iso()
            assert os.path.exists(live.get_liveos())
            assert os.path.isdir(live.get_liveos())
            assert os.path.exists(os.path.join(live.get_liveos(), 'osmin.img'))
            assert os.path.exists(os.path.join(live.get_liveos(),
                'squashfs.img'))
            assert os.path.isdir(os.path.join(os.path.dirname(
                live.get_liveos()), 'isolinux'))
            assert os.path.exists(os.path.join(os.path.dirname(
                live.get_liveos()), 'isolinux', 'isolinux.cfg'))
            assert os.path.exists(os.path.join(os.path.dirname(
                live.get_liveos()), 'isolinux', 'vmlinuz0'))

    def test_mbr(self):
        """ Ensure that we can properly detect and reset a blank MBR """
        live = self._get_creator()
        live.detect_removable_drives()

        for drive in live.drives:
            live.drive = drive

            # Wipe out our MBR
            live.popen('dd if=/dev/zero of=%s bs=2 count=1' % drive)
            assert live.blank_mbr()

            # Reset the MBR
            live.reset_mbr()
            assert not live.blank_mbr()
