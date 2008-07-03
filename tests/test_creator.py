
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

    def test_releases(self):
        from liveusb.releases import releases
        assert releases and len(releases)
        for release in releases:
            assert release['name']
            assert release['url']
            assert release['sha1'] and len(release['sha1']) == 40
