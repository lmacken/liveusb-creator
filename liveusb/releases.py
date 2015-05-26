import re
import traceback

from urlgrabber import urlread
from urlgrabber.grabber import URLGrabError

BASE_URL = 'https://dl.fedoraproject.org'
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
                                if release >= 22:
                                    # SHA256 (filename) = checksum
                                    if '=' in line:
                                        try:
                                            hash_type, filename, _, sha256 = line.split()
                                            filename = filename[1:-1]
                                            name = filename.replace('.iso', '')
                                            fedora_releases.append(dict(
                                                name=name,
                                                url=arch_url + filename,
                                                sha256=sha256,
                                            ))
                                        except ValueError:
                                            pass
                                else:
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
 {'name': 'Fedora-Live-Workstation-x86_64-22-3',
  'sha256': '615abfc89709a46a078dd1d39638019aa66f62b0ff8325334f1af100551bb6cf',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/22/Workstation/x86_64/iso/Fedora-Live-Workstation-x86_64-22-3.iso'},
 {'name': 'Fedora-Workstation-netinst-x86_64-22',
  'sha256': 'c9d22e708b21336582b19b336b7063fc4b882be4cf96d4d0693de07bd66c25e8',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/22/Workstation/x86_64/iso/Fedora-Workstation-netinst-x86_64-22.iso'},
 {'name': 'Fedora-Live-Workstation-i686-22-3',
  'sha256': '6e4c47b582ece2b431ee95d6f453945d11e28c712f7619b178cb31979138f884',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/22/Workstation/i386/iso/Fedora-Live-Workstation-i686-22-3.iso'},
 {'name': 'Fedora-Workstation-netinst-i386-22',
  'sha256': 'f223182829022fbabb4321e6c21e43ec515d5446e17b340f6a87496e9b14a6f7',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/22/Workstation/i386/iso/Fedora-Workstation-netinst-i386-22.iso'},
 {'name': 'Fedora-Server-DVD-x86_64-22',
  'sha256': 'b2acfa7c7c6b5d2f51d3337600c2e52eeaa1a1084991181c28ca30343e52e0df',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/22/Server/x86_64/iso/Fedora-Server-DVD-x86_64-22.iso'},
 {'name': 'Fedora-Server-netinst-x86_64-22',
  'sha256': '9f1f2f19f75cc3b97da41878b5c86188fa8d27ed446bd97d9df615c137c77cfc',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/22/Server/x86_64/iso/Fedora-Server-netinst-x86_64-22.iso'},
 {'name': 'Fedora-Server-DVD-i386-22',
  'sha256': '5e3dfdff30667f3339d8b4e6ac0651c2e00c9417987848bef772cb92dbc823a5',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/22/Server/i386/iso/Fedora-Server-DVD-i386-22.iso'},
 {'name': 'Fedora-Server-netinst-i386-22',
  'sha256': '39df8a90c82ad62b1f1afe25bcb1fed7324179c9ba91d2278c72798721d3702f',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/22/Server/i386/iso/Fedora-Server-netinst-i386-22.iso'},
 {'name': 'Fedora-Live-KDE-x86_64-22-3',
  'sha256': '0ccfbe7a2233cff2496aee037e3320471eb4de42ada2e27018cf5ac7adc14fdd',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/22/Live/x86_64/Fedora-Live-KDE-x86_64-22-3.iso'},
 {'name': 'Fedora-Live-LXDE-x86_64-22-3',
  'sha256': '6a444fd233068e0ebebaed665453dd7238d1f7b8cc0930b7dd1c8a866ca0d90b',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/22/Live/x86_64/Fedora-Live-LXDE-x86_64-22-3.iso'},
 {'name': 'Fedora-Live-MATE_Compiz-x86_64-22-3',
  'sha256': '2bb1eb56d3cb0bd0f645fa3deac8489ea9cef1c6ca57115f87cfc5e2bd844175',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/22/Live/x86_64/Fedora-Live-MATE_Compiz-x86_64-22-3.iso'},
 {'name': 'Fedora-Live-SoaS-x86_64-22-3',
  'sha256': 'fc637d47f1590d3cc4f4ad2c725508238c40bdeb9b00dc1ecf1ea5e0f9093d41',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/22/Live/x86_64/Fedora-Live-SoaS-x86_64-22-3.iso'},
 {'name': 'Fedora-Live-Xfce-x86_64-22-3',
  'sha256': '08f1c79845b8e6a357aeeba42c7719db0d088d8dbf2df078b3202d2392b18949',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/22/Live/x86_64/Fedora-Live-Xfce-x86_64-22-3.iso'},
 {'name': 'Fedora-Live-KDE-i686-22-3',
  'sha256': 'de9b7f049b3c7c10101537e26f3ac9392ca0e9846c3e6bfd63d23f9e7ba8612d',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/22/Live/i386/Fedora-Live-KDE-i686-22-3.iso'},
 {'name': 'Fedora-Live-LXDE-i686-22-3',
  'sha256': '2301cd9b664fc97602152da8550c6876e70859362c24fc183cd16cd398cac0d6',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/22/Live/i386/Fedora-Live-LXDE-i686-22-3.iso'},
 {'name': 'Fedora-Live-MATE_Compiz-i686-22-3',
  'sha256': '3a1cb11c1d70d0a4c96f028ef59cf5dc3ae1379540556a8413430b85437ab527',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/22/Live/i386/Fedora-Live-MATE_Compiz-i686-22-3.iso'},
 {'name': 'Fedora-Live-SoaS-i686-22-3',
  'sha256': '2c9928cb0aa505e011938ede1105da201f3414e1d80787ac079067d0c503cd8f',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/22/Live/i386/Fedora-Live-SoaS-i686-22-3.iso'},
 {'name': 'Fedora-Live-Xfce-i686-22-3',
  'sha256': '4b76fe7db8ee2ad24499e84abfa6830b4f75f45b5772cfcc905ea928cb6852ae',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/22/Live/i386/Fedora-Live-Xfce-i686-22-3.iso'},
 {'name': 'Fedora-Live-Design_suite-x86_64-22-3',
  'sha256': 'c59e48d7ff05424465e20790083049f774e49f0906554bdec36d419a3149f3ac',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/22/Spins/x86_64/Fedora-Live-Design_suite-x86_64-22-3.iso'},
 {'name': 'Fedora-Live-Games-x86_64-22-3',
  'sha256': 'b412cba2accfa7150621609ef34c79a46417fb47322d7db64a548c765ffa2354',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/22/Spins/x86_64/Fedora-Live-Games-x86_64-22-3.iso'},
 {'name': 'Fedora-Live-Jam_KDE-x86_64-22-3',
  'sha256': 'e7b376161a293a877d187a2cfab49c147810f8e56729d0a1530f02446499277b',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/22/Spins/x86_64/Fedora-Live-Jam_KDE-x86_64-22-3.iso'},
 {'name': 'Fedora-Live-Robotics-x86_64-22-3',
  'sha256': '06e4d9144b4a5bc57b3fc97827eb18537faea2e6df887b444a5cbfa519a1ab27',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/22/Spins/x86_64/Fedora-Live-Robotics-x86_64-22-3.iso'},
 {'name': 'Fedora-Live-Scientific_KDE-x86_64-22-3',
  'sha256': '060a54263da91160f50b30ea3a2bb96c92dca1c0766b9e7cc2dde6cfc3221335',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/22/Spins/x86_64/Fedora-Live-Scientific_KDE-x86_64-22-3.iso'},
 {'name': 'Fedora-Live-Security-x86_64-22-3',
  'sha256': '52906c1767716098a059940d675a7ff7ba781b72e75924259effdbd426af72aa',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/22/Spins/x86_64/Fedora-Live-Security-x86_64-22-3.iso'},
 {'name': 'Fedora-Live-Design_suite-i686-22-3',
  'sha256': '474d101a6fd30e6a8a91bb18a02996b93d96b71423eb1bd6d8e14334215c1f86',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/22/Spins/i386/Fedora-Live-Design_suite-i686-22-3.iso'},
 {'name': 'Fedora-Live-Games-i686-22-3',
  'sha256': 'e4d318e193148756fcf61868f8d51a0a21ea347ea33c0af5da16a384d80a6dd8',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/22/Spins/i386/Fedora-Live-Games-i686-22-3.iso'},
 {'name': 'Fedora-Live-Jam_KDE-i686-22-3',
  'sha256': '0026c11cb89f07df96c12d2a414418160963a39872e1faadc0d9bbd5e4c90aa2',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/22/Spins/i386/Fedora-Live-Jam_KDE-i686-22-3.iso'},
 {'name': 'Fedora-Live-Robotics-i686-22-3',
  'sha256': '5d6afbed4dfaf822c1cd86ba8605a6e8ebced5aaf563063147c43ad6380559b0',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/22/Spins/i386/Fedora-Live-Robotics-i686-22-3.iso'},
 {'name': 'Fedora-Live-Scientific_KDE-i686-22-3',
  'sha256': '286e48dafc6a8ba0f22a482e6ff4f00e71f62ab919858e95b58ce6117a7bc322',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/22/Spins/i386/Fedora-Live-Scientific_KDE-i686-22-3.iso'},
 {'name': 'Fedora-Live-Security-i686-22-3',
  'sha256': 'acb327698c63cc2fa533d6ad1be122701c728927c690cfc21043a22276d3aa68',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/22/Spins/i386/Fedora-Live-Security-i686-22-3.iso'},
 {'name': 'Fedora-Live-Workstation-x86_64-21-5',
  'sha256': '4b8418fa846f7dd00e982f3951853e1a4874a1fe023415ae27a5ee313fc98998',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/21/Workstation/x86_64/iso/Fedora-Live-Workstation-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-Workstation-i686-21-5',
  'sha256': 'e0f189a0539a149ceb34cb2b28260db7780f348443b756904e6a250474953f69',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/21/Workstation/i386/iso/Fedora-Live-Workstation-i686-21-5.iso'},
 {'name': 'Fedora-Server-DVD-x86_64-21',
  'sha256': 'a6a2e83bb409d6b8ee3072ad07faac0a54d79c9ecbe3a40af91b773e2d843d8e',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/21/Server/x86_64/iso/Fedora-Server-DVD-x86_64-21.iso'},
 {'name': 'Fedora-Server-netinst-x86_64-21',
  'sha256': '56af126a50c227d779a200b414f68ea7bcf58e21c8035500cd21ba164f85b9b4',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/21/Server/x86_64/iso/Fedora-Server-netinst-x86_64-21.iso'},
 {'name': 'Fedora-Server-DVD-i386-21',
  'sha256': '85e50a8a938996522bf1605b3578a2d6680362c1aa963d0560d59c2e4fc795ef',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/21/Server/i386/iso/Fedora-Server-DVD-i386-21.iso'},
 {'name': 'Fedora-Server-netinst-i386-21',
  'sha256': 'a39648334cbf515633f4a70b405a8fbee2662d1e7d1ad686a6861d9e1667e86c',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/21/Server/i386/iso/Fedora-Server-netinst-i386-21.iso'},
 {'name': 'Fedora-Cloud-netinst-x86_64-21',
  'sha256': 'be73df48aed44aec7e995cf057d6b8cba7b58c78fb657eb8076376662ec5bd69',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/21/Cloud/x86_64/iso/Fedora-Cloud-netinst-x86_64-21.iso'},
 {'name': 'Fedora-Cloud-netinst-i386-21',
  'sha256': 'b3a169cb8f5b60cec0560d78f826b49384366f4a54434867d6bd90f590a6b9fc',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/21/Cloud/i386/iso/Fedora-Cloud-netinst-i386-21.iso'},
 {'name': 'Fedora-Live-KDE-x86_64-21-5',
  'sha256': '8459bca9e1005a0bb5ccba377f2908eda75e3ec89ae87f2a4a7b520f673f3b02',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/21/Live/x86_64/Fedora-Live-KDE-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-LXDE-x86_64-21-5',
  'sha256': '55b7c71cdab30ad393dc45fe147a711064e41bb2a62a420025734a33d9b159b6',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/21/Live/x86_64/Fedora-Live-LXDE-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-MATE_Compiz-x86_64-21-5',
  'sha256': 'b569c6b78566a365036650ff401984569b005827143a25b4b38a3d9e03d05e4c',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/21/Live/x86_64/Fedora-Live-MATE_Compiz-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-SoaS-x86_64-21-5',
  'sha256': '0eb962a0666006f1f2bfcd013c01a09f79af773e9325679a68009a7ff5082ed9',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/21/Live/x86_64/Fedora-Live-SoaS-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-Xfce-x86_64-21-5',
  'sha256': 'f264e9d43a7ce8eff70fb623954c5aafeb074bc0d182c7b5166c1b64ce1b66df',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/21/Live/x86_64/Fedora-Live-Xfce-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-KDE-i686-21-5',
  'sha256': '3a16ee37c9795b6004f31d294af28591cea05ca97c92699fa725eec2352fac71',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/21/Live/i386/Fedora-Live-KDE-i686-21-5.iso'},
 {'name': 'Fedora-Live-LXDE-i686-21-5',
  'sha256': '306787c561b526372ed95c3cadb3ea5dce8d1c6e30fa501662f18651b43a3d34',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/21/Live/i386/Fedora-Live-LXDE-i686-21-5.iso'},
 {'name': 'Fedora-Live-MATE_Compiz-i686-21-5',
  'sha256': '7cb18731396aa1b364408f42f3795b3b6665f141b1be75e9cba4e4d89bb3c8ec',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/21/Live/i386/Fedora-Live-MATE_Compiz-i686-21-5.iso'},
 {'name': 'Fedora-Live-SoaS-i686-21-5',
  'sha256': '1b1b5d4a86e4e2779a4a6137e966fe561a4d694794e3fb60c9b55d71d11e1265',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/21/Live/i386/Fedora-Live-SoaS-i686-21-5.iso'},
 {'name': 'Fedora-Live-Xfce-i686-21-5',
  'sha256': 'cfed2432ce535f309bb439af3b02163b0251313ad77be725189395c137e2fe9d',
  'url': 'https://dl.fedoraproject.org/pub/fedora/linux/releases/21/Live/i386/Fedora-Live-Xfce-i686-21-5.iso'},
 {'name': 'Fedora-Live-Design_suite-x86_64-21-5',
  'sha256': 'bc81fc61940243795207ea43fe73f280e56bdcd2c454306732e33e214165ef20',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/21/Spins/x86_64/Fedora-Live-Design_suite-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-Electronic_Lab-x86_64-21-5',
  'sha256': 'b054004b09aaaa2dd30472de705c956591fcaba17bc20f1eb61ac61bddd7167a',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/21/Spins/x86_64/Fedora-Live-Electronic_Lab-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-Games-x86_64-21-5',
  'sha256': 'c5fdcb86d36b896a7f6bfaa04287d78f4512ce1c832b31cf08a3d47018223a5e',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/21/Spins/x86_64/Fedora-Live-Games-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-Jam_KDE-x86_64-21-5',
  'sha256': 'def1f1c08cd1154d0c47900f4883c0efcd3b12f3f42e14cab8a3f40a10d41305',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/21/Spins/x86_64/Fedora-Live-Jam_KDE-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-Robotics-x86_64-21-5',
  'sha256': 'd0bdd7595b8980354ad594ebab9719e8b58bdff621cec39629f3836c99b3e54e',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/21/Spins/x86_64/Fedora-Live-Robotics-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-Scientific_KDE-x86_64-21-5',
  'sha256': 'a03ce7eba41d5a517eb5f4ddcd882e68363ffb1e9cce6f8153712a7b9e98eb5f',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/21/Spins/x86_64/Fedora-Live-Scientific_KDE-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-Security-x86_64-21-5',
  'sha256': '08d5e063d69889da9be6677f4d2e07c1ef5df9dcf10689e0f57bea9f974cb98b',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/21/Spins/x86_64/Fedora-Live-Security-x86_64-21-5.iso'},
 {'name': 'Fedora-Live-Design_suite-i686-21-5',
  'sha256': '6ab0aff1888d054853c27fd57618a1dcfa7bfabd66c47268c6f6546474db2914',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/21/Spins/i386/Fedora-Live-Design_suite-i686-21-5.iso'},
 {'name': 'Fedora-Live-Electronic_Lab-i686-21-5',
  'sha256': '212cb78b1146b06dff1207f231c3d278b4c75c7faff25c2347626f1ee942fd0d',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/21/Spins/i386/Fedora-Live-Electronic_Lab-i686-21-5.iso'},
 {'name': 'Fedora-Live-Games-i686-21-5',
  'sha256': '6866989da6394daa63648084e345b160a5ea659bb3333ce8c19b1b4d92c29d98',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/21/Spins/i386/Fedora-Live-Games-i686-21-5.iso'},
 {'name': 'Fedora-Live-Jam_KDE-i686-21-5',
  'sha256': '6f638a5fb437091886af144092b727cf4767a919b10d69d0b4b4f786e92497ed',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/21/Spins/i386/Fedora-Live-Jam_KDE-i686-21-5.iso'},
 {'name': 'Fedora-Live-Robotics-i686-21-5',
  'sha256': '0814a39a185b66f237ed7ba8f4bc8fdd3a1fe345fec5d4376b5b38a0b28e7d22',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/21/Spins/i386/Fedora-Live-Robotics-i686-21-5.iso'},
 {'name': 'Fedora-Live-Scientific_KDE-i686-21-5',
  'sha256': '4df33ad5350f5ad671ab82c9ed4681cf4240495921d173bafbcc8a5cd163492c',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/21/Spins/i386/Fedora-Live-Scientific_KDE-i686-21-5.iso'},
 {'name': 'Fedora-Live-Security-i686-21-5',
  'sha256': 'bd40a188388f6074cd8258f55a0da1d72f19479c1aea2e68d96380c7f92d99e5',
  'url': 'https://dl.fedoraproject.org/pub/alt/releases/21/Spins/i386/Fedora-Live-Security-i686-21-5.iso'}
]

releases = fedora_releases

if __name__ == '__main__':
    import pprint
    pprint.pprint(get_fedora_releases())
