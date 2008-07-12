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
            assert release['sha1'] and len(release['sha1']) == 40

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
