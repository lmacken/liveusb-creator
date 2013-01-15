import re
from urlgrabber import urlread
from urlgrabber.grabber import URLGrabError

FEDORA_RELEASES = 'http://dl.fedoraproject.org/pub/fedora/linux/releases/'
ARCHES = ('i386', 'i686', 'x86_64')

def get_fedora_releases():
    releases = []
    html = urlread(FEDORA_RELEASES)
    for release in re.findall(r'<a href="(\d+)/">', html)[-2:][::-1]:
        for arch in ARCHES:
            arch_url = FEDORA_RELEASES + '%s/Live/%s/' % (release, arch)
            try:
                files = urlread(arch_url)
            except URLGrabError:
                continue
            for link in re.findall(r'<a href="(.*)">', files):
                if link.endswith('-CHECKSUM'):
                    checksum = urlread(arch_url + link)
                    for line in checksum.split('\n'):
                        try:
                            sha256, filename = line.split()
                            if filename[0] != '*':
                                continue
                            filename = filename[1:]
                            chunks = filename[:-4].split('-')
                            chunks.remove('Live')
                            name = ' '.join(chunks)
                            releases.append(dict(
                                name = name,
                                url = arch_url + filename,
                                sha256 = sha256,
                                ))
                        except ValueError:
                            pass
    return releases


from pprint import pprint
pprint(get_fedora_releases())
