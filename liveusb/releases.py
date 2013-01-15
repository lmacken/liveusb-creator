import re
from urlgrabber import urlread
from urlgrabber.grabber import URLGrabError

FEDORA_RELEASES = 'http://dl.fedoraproject.org/pub/fedora/linux/releases/'
ARCHES = ('i386', 'i686', 'x86_64')

# A backup list of releases, just in case we can't fetch them.
fedora_releases = [
    {'name': 'Fedora 18 i686 Desktop',
     'sha256': '7c7f453c15a5d13df95bf8caab6277e5aab1c6353eb242b1cf00344b61869d26',
     'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/18/Live/i386/Fedora-18-i686-Live-Desktop.iso'},
    {'name': 'Fedora 18 i686 KDE',
     'sha256': 'f172192566d0e12c29a741a568a917c5d8643aa781fdf06598b12a217a58cb74',
     'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/18/Live/i386/Fedora-18-i686-Live-KDE.iso'},
    {'name': 'Fedora 18 x86_64 Desktop',
     'sha256': 'a276e06d244e04b765f0a35532d9036ad84f340b0bdcc32e0233a8fbc31d5bed',
     'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/18/Live/x86_64/Fedora-18-x86_64-Live-Desktop.iso'},
    {'name': 'Fedora 18 x86_64 KDE',
     'sha256': '41d51d86ff5c272263285d00a0c3da7acbbce404b9930b0ff8bd7226e7248805',
     'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/18/Live/x86_64/Fedora-18-x86_64-Live-KDE.iso'},
    {'name': 'Fedora 17 i686 Desktop',
     'sha256': '26027f4d4686f1df186b31ce773dbb903db18f4b1aa37a1e37f0fa6ff4111f42',
     'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/17/Live/i686/Fedora-17-i686-Live-Desktop.iso'},
    {'name': 'Fedora 17 i686 KDE',
     'sha256': 'f10142bb0a4d91a0d8320a925fa33ab3a87d9764b03137bb30506830c1068583',
     'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/17/Live/i686/Fedora-17-i686-Live-KDE.iso'},
    {'name': 'Fedora 17 x86_64 Desktop',
     'sha256': 'dfd19d677790fea6144bcf537cd031dfb0a50e6c56652c94bfc71ea7bb949f2c',
     'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/17/Live/x86_64/Fedora-17-x86_64-Live-Desktop.iso'},
    {'name': 'Fedora 17 x86_64 KDE',
     'sha256': '58b9abf5ef6a07b75b6a934468c783ab18e5a1236e6e5ab75dc2b39ca7680462',
     'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/17/Live/x86_64/Fedora-17-x86_64-Live-KDE.iso'},
    {'name': 'Fedora 16 i686 Desktop',
     'sha256': '561d2c15fa79c319959cfc821650c829860651d1e5b125b2a425ac9cbd3fe1bb',
     'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/16/Live/i686/Fedora-16-i686-Live-Desktop.iso'},
    {'name': 'Fedora 16 i686 KDE',
     'sha256': '822567e4b05f7be6b89c14e6165f4c9e0f388379c3f90e0bf439dd8397e87a3f',
     'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/16/Live/i686/Fedora-16-i686-Live-KDE.iso'},
    {'name': 'Fedora 16 x86_64 Desktop',
     'sha256': '632b2de39033ed1d4a61959c4002e07248793eff828ac5d60edbb7b5dcd7be5c',
     'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/16/Live/x86_64/Fedora-16-x86_64-Live-Desktop.iso'},
    {'name': 'Fedora 16 x86_64 KDE',
     'sha256': 'b10ff86610e46244b11f0a411915e80ca4fdf1e8ec20ee5b61f700feb0716ba8',
     'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/16/Live/x86_64/Fedora-16-x86_64-Live-KDE.iso'},
]

other_releases = [
    ##
    ## Custom spins
    ##
    {
        'name': 'Sugar on a Stick v6 Pineapple',
        'url': 'https://alt.fedoraproject.org/pub/alt/spins/linux/releases/16/Spins/i686/Fedora-16-i686-Live-SoaS.iso',
        'sha256': '5aa938737cc4ebeb1d269c4d8b2bf56e41bacd1967c3997b8969b42b88b63bfa',
    },
]

releases = fedora_releases + other_releases


def get_fedora_releases():
    global releases
    fedora_releases = []
    try:
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
