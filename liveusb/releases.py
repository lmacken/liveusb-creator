import re
from urlgrabber import urlread
from urlgrabber.grabber import URLGrabError

FEDORA_RELEASES = 'http://dl.fedoraproject.org/pub/fedora/linux/releases/'
ARCHES = ('armhfp', 'x86_64', 'i686', 'i386')

# A backup list of releases, just in case we can't fetch them.
fedora_releases = [
    {'name': 'Fedora 20 x86_64 Desktop',
     'sha256': 'cc0333be93c7ff2fb3148cb29360d2453f78913cc8aa6c6289ae6823372a77d2',
     'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/20/Live/x86_64/Fedora-Live-Desktop-x86_64-20-1.iso'},
    {'name': 'Fedora 20 x86_64 KDE',
     'sha256': '08360a253b4a40dff948e568dba1d2ae9d931797f57aa08576b8b9f1ef7e4745',
     'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/20/Live/x86_64/Fedora-Live-KDE-x86_64-20-1.iso'},
    {'name': 'Fedora 20 i686 Desktop',
     'sha256': 'b115c5653b855de2353e41ff0c72158350f14a020c041462f35ba2a47bd1e33b',
     'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/20/Live/i386/Fedora-Live-Desktop-i686-20-1.iso'},
    {'name': 'Fedora 20 i686 KDE',
     'sha256': 'd859132ea9496994ccbb5d6e60c9f40ae89ba31f8a4a1a2a883d6d45901de598',
     'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/20/Live/i386/Fedora-Live-KDE-i686-20-1.iso'},
    {'name': 'Fedora 19 x86_64 Desktop',
     'sha256': '21f0197284b9088b32d683f83a71bd42261f1df885a63b1eb87254d1ca096f12',
     'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/19/Live/x86_64/Fedora-Live-Desktop-x86_64-19-1.iso'},
    {'name': 'Fedora 19 x86_64 KDE',
     'sha256': 'f4479d5639f62d7398722c6a432ba94711b80d5011d5b64e7afebb4f4ac10cf7',
     'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/19/Live/x86_64/Fedora-Live-KDE-x86_64-19-1.iso'},
    {'name': 'Fedora 19 i686 Desktop',
     'sha256': 'ce9797802ef1f7aa670fffd04f209631c171b8ded5dc26f61df898cb9441c839',
     'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/19/Live/i386/Fedora-Live-Desktop-i686-19-1.iso'},
    {'name': 'Fedora 19 i686 KDE',
     'sha256': 'e81717564f96ee0f8c6d8b0186e7fca44da57f2ef154ea427b6d765ea139a083',
     'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/19/Live/i386/Fedora-Live-KDE-i686-19-1.iso'},
]

other_releases = [
    ##
    ## Custom spins
    ##
    {
        'name': 'Sugar on a Stick v10 (x86_64)',
        'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/20/Live/x86_64/Fedora-Live-SoaS-x86_64-20-1.iso',
        'sha256': 'b1865e40e57ed5c4bb705f95e3190c5e56ca6ed9c34f53b16e8c45ccb1233be8',
    },
    {
        'name': 'Sugar on a Stick v10 (i686)',
        'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/20/Live/i386/Fedora-Live-SoaS-i686-20-1.iso',
        'sha256': 'efe76d842a7e19a5ee66461bf51a9cf649d426d007841a5f06f14851dceab389',
    },
]

releases = fedora_releases + other_releases


def get_fedora_releases():
    global releases
    fedora_releases = []
    try:
        html = urlread(FEDORA_RELEASES)
        versions = re.findall(r'<a href="(\d+)/">', html)
        latest = sorted([int(v) for v in versions], reverse=True)[0:2]
        for release in latest:
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
                                chunks = filename[:-6].split('-')
                                chunks.remove('Live')
                                release = chunks.pop()
                                chunks.insert(1,release)
                                name = ' '.join(chunks)
                                fedora_releases.append(dict(
                                    name=name,
                                    url=arch_url + filename,
                                    sha256=sha256,
                                ))
                            except ValueError:
                                pass
        releases = fedora_releases + other_releases
    except:
        # Can't fetch releases from the internet.
        releases += other_releases
    return releases
