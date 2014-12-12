import re
import traceback

from urlgrabber import urlread
from urlgrabber.grabber import URLGrabError

BASE_URL = 'http://dl.fedoraproject.org'
PUB_URL = BASE_URL + '/pub/fedora/linux/releases/'
ALT_URL = BASE_URL + '/pub/alt/releases/'
ARCHES = ('armhfp', 'x86_64', 'i686', 'i386')


def get_fedora_releases():
    global releases
    fedora_releases = []
    try:
        html = urlread(PUB_URL)
        versions = re.findall(r'<a href="(\d+)/">', html)
        latest = sorted([int(v) for v in versions], reverse=True)[0:2]
        for release in latest:
            if release >= 21:
                products = ('Workstation', 'Server', 'Cloud', 'Live', 'Spins')
            else:
                products = ('Live', 'Spins')
            for product in products:
                for arch in ARCHES:
                    baseurl = PUB_URL
                    if product == 'Live':
                        isodir = '/'
                    elif product == 'Spins':
                        baseurl = ALT_URL
                        isodir = '/'
                    else:
                        isodir = '/iso/'
                    arch_url = baseurl + '%s/%s/%s%s' % (release,
                            product, arch, isodir)
                    print(arch_url)
                    try:
                        files = urlread(arch_url)
                    except URLGrabError:
                        continue
                    for link in re.findall(r'<a href="(.*)">', files):
                        if link.endswith('-CHECKSUM'):
                            print('Reading %s' % arch_url + link)
                            checksum = urlread(arch_url + link)
                            for line in checksum.split('\n'):
                                try:
                                    sha256, filename = line.split()
                                    if filename[0] != '*':
                                        continue
                                    filename = filename[1:]
                                    name = filename.replace('.iso', '')
                                    fedora_releases.append(dict(
                                        name=name,
                                        url=arch_url + filename,
                                        sha256=sha256,
                                    ))
                                except ValueError:
                                    pass
        releases = fedora_releases
    except:
        traceback.print_exc()
    return releases


# A backup list of releases, just in case we can't fetch them.
fedora_releases = [
 {'name': 'Fedora-Live-Workstation-x86_64-21-5',
  'sha256': '4b8418fa846f7dd00e982f3951853e1a4874a1fe023415ae27a5ee313fc98998',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/21/Workstation/x86_64/iso/Fedora-Live-Workstation-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-Workstation-i686-21-5',
  'sha256': 'e0f189a0539a149ceb34cb2b28260db7780f348443b756904e6a250474953f69',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/21/Workstation/i386/iso/Fedora-Live-Workstation-i686-21-5.iso'},
 {'name': 'Fedora-Server-DVD-x86_64-21',
  'sha256': 'a6a2e83bb409d6b8ee3072ad07faac0a54d79c9ecbe3a40af91b773e2d843d8e',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/21/Server/x86_64/iso/Fedora-Server-DVD-x86_64-21.iso'},
 {'name': 'Fedora-Server-netinst-x86_64-21',
  'sha256': '56af126a50c227d779a200b414f68ea7bcf58e21c8035500cd21ba164f85b9b4',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/21/Server/x86_64/iso/Fedora-Server-netinst-x86_64-21.iso'},
 {'name': 'Fedora-Server-DVD-i386-21',
  'sha256': '85e50a8a938996522bf1605b3578a2d6680362c1aa963d0560d59c2e4fc795ef',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/21/Server/i386/iso/Fedora-Server-DVD-i386-21.iso'},
 {'name': 'Fedora-Server-netinst-i386-21',
  'sha256': 'a39648334cbf515633f4a70b405a8fbee2662d1e7d1ad686a6861d9e1667e86c',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/21/Server/i386/iso/Fedora-Server-netinst-i386-21.iso'},
 {'name': 'Fedora-Cloud-netinst-x86_64-21',
  'sha256': 'be73df48aed44aec7e995cf057d6b8cba7b58c78fb657eb8076376662ec5bd69',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/21/Cloud/x86_64/iso/Fedora-Cloud-netinst-x86_64-21.iso'},
 {'name': 'Fedora-Cloud-netinst-i386-21',
  'sha256': 'b3a169cb8f5b60cec0560d78f826b49384366f4a54434867d6bd90f590a6b9fc',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/21/Cloud/i386/iso/Fedora-Cloud-netinst-i386-21.iso'},
 {'name': 'Fedora-Live-KDE-x86_64-21-5',
  'sha256': '8459bca9e1005a0bb5ccba377f2908eda75e3ec89ae87f2a4a7b520f673f3b02',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/21/Live/x86_64/Fedora-Live-KDE-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-LXDE-x86_64-21-5',
  'sha256': '55b7c71cdab30ad393dc45fe147a711064e41bb2a62a420025734a33d9b159b6',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/21/Live/x86_64/Fedora-Live-LXDE-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-MATE_Compiz-x86_64-21-5',
  'sha256': 'b569c6b78566a365036650ff401984569b005827143a25b4b38a3d9e03d05e4c',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/21/Live/x86_64/Fedora-Live-MATE_Compiz-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-SoaS-x86_64-21-5',
  'sha256': '0eb962a0666006f1f2bfcd013c01a09f79af773e9325679a68009a7ff5082ed9',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/21/Live/x86_64/Fedora-Live-SoaS-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-Xfce-x86_64-21-5',
  'sha256': 'f264e9d43a7ce8eff70fb623954c5aafeb074bc0d182c7b5166c1b64ce1b66df',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/21/Live/x86_64/Fedora-Live-Xfce-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-KDE-i686-21-5',
  'sha256': '3a16ee37c9795b6004f31d294af28591cea05ca97c92699fa725eec2352fac71',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/21/Live/i386/Fedora-Live-KDE-i686-21-5.iso'},
 {'name': 'Fedora-Live-LXDE-i686-21-5',
  'sha256': '306787c561b526372ed95c3cadb3ea5dce8d1c6e30fa501662f18651b43a3d34',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/21/Live/i386/Fedora-Live-LXDE-i686-21-5.iso'},
 {'name': 'Fedora-Live-MATE_Compiz-i686-21-5',
  'sha256': '7cb18731396aa1b364408f42f3795b3b6665f141b1be75e9cba4e4d89bb3c8ec',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/21/Live/i386/Fedora-Live-MATE_Compiz-i686-21-5.iso'},
 {'name': 'Fedora-Live-SoaS-i686-21-5',
  'sha256': '1b1b5d4a86e4e2779a4a6137e966fe561a4d694794e3fb60c9b55d71d11e1265',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/21/Live/i386/Fedora-Live-SoaS-i686-21-5.iso'},
 {'name': 'Fedora-Live-Xfce-i686-21-5',
  'sha256': 'cfed2432ce535f309bb439af3b02163b0251313ad77be725189395c137e2fe9d',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/21/Live/i386/Fedora-Live-Xfce-i686-21-5.iso'},
 {'name': 'Fedora-Live-Design_suite-x86_64-21-5',
  'sha256': 'bc81fc61940243795207ea43fe73f280e56bdcd2c454306732e33e214165ef20',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/21/Spins/x86_64/Fedora-Live-Design_suite-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-Electronic_Lab-x86_64-21-5',
  'sha256': 'b054004b09aaaa2dd30472de705c956591fcaba17bc20f1eb61ac61bddd7167a',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/21/Spins/x86_64/Fedora-Live-Electronic_Lab-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-Games-x86_64-21-5',
  'sha256': 'c5fdcb86d36b896a7f6bfaa04287d78f4512ce1c832b31cf08a3d47018223a5e',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/21/Spins/x86_64/Fedora-Live-Games-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-Jam_KDE-x86_64-21-5',
  'sha256': 'def1f1c08cd1154d0c47900f4883c0efcd3b12f3f42e14cab8a3f40a10d41305',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/21/Spins/x86_64/Fedora-Live-Jam_KDE-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-Robotics-x86_64-21-5',
  'sha256': 'd0bdd7595b8980354ad594ebab9719e8b58bdff621cec39629f3836c99b3e54e',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/21/Spins/x86_64/Fedora-Live-Robotics-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-Scientific_KDE-x86_64-21-5',
  'sha256': 'a03ce7eba41d5a517eb5f4ddcd882e68363ffb1e9cce6f8153712a7b9e98eb5f',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/21/Spins/x86_64/Fedora-Live-Scientific_KDE-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-Security-x86_64-21-5',
  'sha256': '08d5e063d69889da9be6677f4d2e07c1ef5df9dcf10689e0f57bea9f974cb98b',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/21/Spins/x86_64/Fedora-Live-Security-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-Design_suite-i686-21-5',
  'sha256': '6ab0aff1888d054853c27fd57618a1dcfa7bfabd66c47268c6f6546474db2914',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/21/Spins/i386/Fedora-Live-Design_suite-i686-21-5.iso'},
 {'name': 'Fedora-Live-Electronic_Lab-i686-21-5',
  'sha256': '212cb78b1146b06dff1207f231c3d278b4c75c7faff25c2347626f1ee942fd0d',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/21/Spins/i386/Fedora-Live-Electronic_Lab-i686-21-5.iso'},
 {'name': 'Fedora-Live-Games-i686-21-5',
  'sha256': '6866989da6394daa63648084e345b160a5ea659bb3333ce8c19b1b4d92c29d98',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/21/Spins/i386/Fedora-Live-Games-i686-21-5.iso'},
 {'name': 'Fedora-Live-Jam_KDE-i686-21-5',
  'sha256': '6f638a5fb437091886af144092b727cf4767a919b10d69d0b4b4f786e92497ed',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/21/Spins/i386/Fedora-Live-Jam_KDE-i686-21-5.iso'},
 {'name': 'Fedora-Live-Robotics-i686-21-5',
  'sha256': '0814a39a185b66f237ed7ba8f4bc8fdd3a1fe345fec5d4376b5b38a0b28e7d22',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/21/Spins/i386/Fedora-Live-Robotics-i686-21-5.iso'},
 {'name': 'Fedora-Live-Scientific_KDE-i686-21-5',
  'sha256': '4df33ad5350f5ad671ab82c9ed4681cf4240495921d173bafbcc8a5cd163492c',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/21/Spins/i386/Fedora-Live-Scientific_KDE-i686-21-5.iso'},
 {'name': 'Fedora-Live-Security-i686-21-5',
  'sha256': 'bd40a188388f6074cd8258f55a0da1d72f19479c1aea2e68d96380c7f92d99e5',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/21/Spins/i386/Fedora-Live-Security-i686-21-5.iso'},
 {'name': 'Fedora-Live-Desktop-x86_64-20-1',
  'sha256': 'cc0333be93c7ff2fb3148cb29360d2453f78913cc8aa6c6289ae6823372a77d2',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/20/Live/x86_64/Fedora-Live-Desktop-x86_64-20-1.iso'},
 {'name': 'Fedora-Live-KDE-x86_64-20-1',
  'sha256': '08360a253b4a40dff948e568dba1d2ae9d931797f57aa08576b8b9f1ef7e4745',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/20/Live/x86_64/Fedora-Live-KDE-x86_64-20-1.iso'},
 {'name': 'Fedora-Live-LXDE-x86_64-20-1',
  'sha256': 'b5002a697ef0e9e6fe10d0b88da6f7d43dbeb1b2c6dccb274b019123f321487d',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/20/Live/x86_64/Fedora-Live-LXDE-x86_64-20-1.iso'},
 {'name': 'Fedora-Live-MATE-Compiz-x86_64-20-1',
  'sha256': '37a3670955210b11e25af93548e1709973431b385379399952de6ae50567b8aa',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/20/Live/x86_64/Fedora-Live-MATE-Compiz-x86_64-20-1.iso'},
 {'name': 'Fedora-Live-SoaS-x86_64-20-1',
  'sha256': 'b1865e40e57ed5c4bb705f95e3190c5e56ca6ed9c34f53b16e8c45ccb1233be8',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/20/Live/x86_64/Fedora-Live-SoaS-x86_64-20-1.iso'},
 {'name': 'Fedora-Live-Xfce-x86_64-20-1',
  'sha256': 'ebfe836aa708d38b66a7ae6fe685ef327772ece5700861bc7c4e83baef0ceb1b',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/20/Live/x86_64/Fedora-Live-Xfce-x86_64-20-1.iso'},
 {'name': 'Fedora-Live-Desktop-i686-20-1',
  'sha256': 'b115c5653b855de2353e41ff0c72158350f14a020c041462f35ba2a47bd1e33b',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/20/Live/i386/Fedora-Live-Desktop-i686-20-1.iso'},
 {'name': 'Fedora-Live-KDE-i686-20-1',
  'sha256': 'd859132ea9496994ccbb5d6e60c9f40ae89ba31f8a4a1a2a883d6d45901de598',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/20/Live/i386/Fedora-Live-KDE-i686-20-1.iso'},
 {'name': 'Fedora-Live-LXDE-i686-20-1',
  'sha256': 'cdfdaa74946792c3e500e32ac923f35c5a6730add9fa1c0997b7ac9b1f7cecae',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/20/Live/i386/Fedora-Live-LXDE-i686-20-1.iso'},
 {'name': 'Fedora-Live-MATE-Compiz-i686-20-1',
  'sha256': 'f885e1bf4db47c2093f0dfa9ef8861bd47103972e3be69ee47054d2568dacd67',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/20/Live/i386/Fedora-Live-MATE-Compiz-i686-20-1.iso'},
 {'name': 'Fedora-Live-SoaS-i686-20-1',
  'sha256': 'efe76d842a7e19a5ee66461bf51a9cf649d426d007841a5f06f14851dceab389',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/20/Live/i386/Fedora-Live-SoaS-i686-20-1.iso'},
 {'name': 'Fedora-Live-Xfce-i686-20-1',
  'sha256': '7d3c38414e85c956ea8ead7a1ca333559cec9252e6c330794215ad87a9829b77',
  'url': 'http://dl.fedoraproject.org/pub/fedora/linux/releases/20/Live/i386/Fedora-Live-Xfce-i686-20-1.iso'},
 {'name': 'Fedora-Live-Design-suite-x86_64-20-1',
  'sha256': '3c334d7918751dc8318d88bc25da281adfefa07e7c0268cdf4221155328b772a',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/20/Spins/x86_64/Fedora-Live-Design-suite-x86_64-20-1.iso'},
 {'name': 'Fedora-Live-Electronic-Lab-x86_64-20-1',
  'sha256': '3ea4a88c7104de90bc5392681b274d44410c4c249140b6a08332a96d70fc72c6',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/20/Spins/x86_64/Fedora-Live-Electronic-Lab-x86_64-20-1.iso'},
 {'name': 'Fedora-Live-Games-x86_64-20-1',
  'sha256': '3febd35364bd96087dad9c2b4fd19a4275866e4aafff764156708d107d4d2561',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/20/Spins/x86_64/Fedora-Live-Games-x86_64-20-1.iso'},
 {'name': 'Fedora-Live-Jam-KDE-x86_64-20-1',
  'sha256': '348d1ececad7c4a96c94b10c7df35e41c20b645c5ae2f183dc0d132bded570b1',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/20/Spins/x86_64/Fedora-Live-Jam-KDE-x86_64-20-1.iso'},
 {'name': 'Fedora-Live-Robotics-x86_64-20-1',
  'sha256': '29391a57a48f31d51e9e8aa97c44157c47bfe461a3dab6491c2af399b6e35ce2',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/20/Spins/x86_64/Fedora-Live-Robotics-x86_64-20-1.iso'},
 {'name': 'Fedora-Live-Scientific-KDE-x86_64-20-1',
  'sha256': '168077683a13657ebd12ae1022932e159115901ad1b991204a0f5be7c47113b9',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/20/Spins/x86_64/Fedora-Live-Scientific-KDE-x86_64-20-1.iso'},
 {'name': 'Fedora-Live-Security-x86_64-20-1',
  'sha256': '1b03c28fccf6497bb3bb863c75fb4149f56565f4962b691834d47b623e7f28af',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/20/Spins/x86_64/Fedora-Live-Security-x86_64-20-1.iso'},
 {'name': 'Fedora-Live-Design-suite-i686-20-1',
  'sha256': '608ee0be25dc363f56a5b76e383fc3c9f082ffb824e0b0f1a754e917524fff44',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/20/Spins/i386/Fedora-Live-Design-suite-i686-20-1.iso'},
 {'name': 'Fedora-Live-Electronic-Lab-i686-20-1',
  'sha256': '0637665a69fe759364620fddf5f50a3b41d1a51f049a6a158886705009bcfc5e',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/20/Spins/i386/Fedora-Live-Electronic-Lab-i686-20-1.iso'},
 {'name': 'Fedora-Live-Games-i686-20-1',
  'sha256': '5158277d04e55b462665ec1c83fd5cf0b4dd159c5820660bde87d1a27b062b44',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/20/Spins/i386/Fedora-Live-Games-i686-20-1.iso'},
 {'name': 'Fedora-Live-Jam-KDE-i686-20-1',
  'sha256': 'b08a643706229ac701cfebbc328ebe118d467f9620f661939b4877e70b01ab1e',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/20/Spins/i386/Fedora-Live-Jam-KDE-i686-20-1.iso'},
 {'name': 'Fedora-Live-Robotics-i686-20-1',
  'sha256': '77ed1638b454b2a738a0736ed3b1bc29aa10797a4222903e48aa901e44b8833d',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/20/Spins/i386/Fedora-Live-Robotics-i686-20-1.iso'},
 {'name': 'Fedora-Live-Scientific-KDE-i686-20-1',
  'sha256': '09f4582423e30459ba06b4fcc29ba5e59894d4ae50353fce376a82ddb94efdb4',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/20/Spins/i386/Fedora-Live-Scientific-KDE-i686-20-1.iso'},
 {'name': 'Fedora-Live-Security-i686-20-1',
  'sha256': '0030acebc70fb5f1d8efe19204e61263410307f65c192f30571af66711c0c8b9',
  'url': 'http://dl.fedoraproject.org/pub/alt/releases/20/Spins/i386/Fedora-Live-Security-i686-20-1.iso'},
]

releases = fedora_releases
