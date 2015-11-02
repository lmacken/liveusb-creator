# -*- coding: utf-8 -*-

import re
import traceback

from urlgrabber import urlread
from urlgrabber.grabber import URLGrabError

from pyquery import pyquery

from liveusb import _
from PyQt5.QtCore import QDateTime

BASE_URL = 'https://dl.fedoraproject.org'
PUB_URL = BASE_URL + '/pub/fedora/linux/releases/'
ALT_URL = BASE_URL + '/pub/alt/releases/'
ARCHES = ('armhfp', 'x86_64', 'i686', 'i386')

def getArch(url):
    return url.split('/')[-1].split('.')[0].split('-')[3]

def getRelease(download):
    for key in download.keys():
        url = download[key]['url']
        break
    try:
        return str(int(url.split('/')[-1].split('.')[0].split('-')[4]))
    except AttributeError:
        return ''

def getSHA(url):
    baseurl = '/'.join(url.split('/')[:-1])
    filename = url.split('/')[-1]
    try:
        d = pyquery.PyQuery(urlread(baseurl))
    except URLGrabError:
        return ''
    checksum = ''
    for i in d.items('a'):
        if 'CHECKSUM' in i.attr('href'):
            checksum = urlread(baseurl + '/' + i.attr('href'))
            break

    for line in checksum.split('\n'):
        i = re.match(r'^SHA256 \(([^)]+)\) = ([a-f0-9]+)$', line)
        if i:
            if i.group(1) == filename:
                return i.group(2)
    return ''

def getSize(text):
    match = re.search(r'([0-9.]+)[ ]?([KMG])B', text)
    if not match or len(match.groups()) not in [2, 3]:
        return 0
    size = float(match.group(1))
    if match.group(2) == 'G':
        size *= 1024 * 1024 * 1024
    if match.group(2) == 'M':
        size *= 1024 * 1024
    if match.group(2) == 'K':
        size *= 1024
    return int(size)

def getDownload(url):
    d = pyquery.PyQuery(urlread(url))
    ret = dict()
    url = d('a.btn-success').attr('href')
    ret[getArch(url)] = dict(
        url = url,
        sha256 = getSHA(url),
        size = getSize(d('a.btn-success').parent().parent()('h5').text())
    )
    for e in d.items("a"):
        if "32-bit" in e.html().lower() and e.attr("href").endswith(".iso"):
            altUrl = e.attr("href")
            ret[getArch(altUrl)] = dict(
                url = altUrl,
                sha256 = getSHA(altUrl),
                size = getSize(e.text())
            )
            break
    return ret

def getSpinDetails(url, source):
    d = pyquery.PyQuery(urlread(url))
    spin = {
        'name': '',
        'summary': '',
        'description': '',
        'version': '',
        'releaseDate': '',
        'logo': 'qrc:/logo_fedora',
        'screenshots': [],
        'source': '',
        'variants': {'': dict(
            url='',
            sha256='',
            size=0
        )}
    }
    spin['source'] = source

    spin['name'] = d('title').html().strip()
    if not spin['name'].startswith('Fedora'):
        spin['name'] = 'Fedora ' + spin['name']
    screenshot = d('img').filter('.img-responsive').attr('src')
    if screenshot:
        spin['screenshots'].append(url + "/.." + screenshot)

    for i in d('div').filter('.col-sm-8').html().split('\n'):
        #line = i.strip().replace('<p>', '').replace('</p>', '')
        line = i.strip()
        if len(line):
            spin['description'] += line

    download = getDownload(url + "/.." + d('a.btn').attr('href'))
    spin['variants'] = download
    spin['version'] = getRelease(download)
    if spin['version'] == '23':
        spin['releaseDate'] = '2015-11-03'

    if 'KDE Plasma' in spin['name']:
        spin['logo'] = 'qrc:/logo_plasma'
    if 'Xfce' in spin['name']:
        spin['logo'] = 'qrc:/logo_xfce'
    if 'LXDE' in spin['name']:
        spin['logo'] = 'qrc:/logo_lxde'
    if 'MATE' in spin['name']:
        spin['logo'] = 'qrc:/logo_mate'
    if 'Cinnamon' in spin['name']:
        spin['logo'] = 'qrc:/logo_cinnamon'
    if 'SoaS' in spin['name']:
        spin['logo'] = 'qrc:/logo_soas'

    if 'Astronomy' in spin['name']:
        spin['logo'] = 'qrc:/logo_astronomy'
    if 'Design' in spin['name']:
        spin['logo'] = 'qrc:/logo_design'
    if 'Games' in spin['name']:
        spin['logo'] = 'qrc:/logo_games'
    if 'Jam' in spin['name']:
        spin['logo'] = 'qrc:/logo_jam'
    if 'Robotics' in spin['name']:
        spin['logo'] = 'qrc:/logo_robotics'
    if 'Scientific' in spin['name']:
        spin['logo'] = 'qrc:/logo_scientific'
    if 'Security' in spin['name']:
        spin['logo'] = 'qrc:/logo_security'

    return spin

def getSpins(url, source):
    d = pyquery.PyQuery(urlread(url))
    spins = []

    if source == 'Spins':
        spins.append({'version': '', 'releaseDate': '', 'source': '', 'name': 'Fedora ' + source, 'logo': '', 'description': '', 'screenshots': [], 'variants': {}, 'summary': 'Alternative desktops for Fedora'})
    elif source == 'Labs':
        spins.append({'version': '', 'releaseDate': '', 'source': '', 'name': 'Fedora ' + source, 'logo': '', 'description': '', 'screenshots': [], 'variants': {}, 'summary': 'Functional bundles for Fedora'})

    for i in d('div').filter('.high').items('span'):
        spinUrl = url + i.siblings()('a').attr('href')
        spin = getSpinDetails(spinUrl, source)
        spin['summary'] = i.html()
        spins.append(spin)

    return spins

def getProductDetails(url):
    d = pyquery.PyQuery(urlread(url))
    product = {
        'name': '',
        'summary': '',
        'description': '',
        'version': '',
        'releaseDate': '',
        'logo': 'qrc:/logo_fedora',
        'screenshots': [],
        'source': '',
        'variants': {'': dict(
            url='',
            sha256='',
            size=0
        )}
    }
    name = d('title').html()

    product['name'] = name
    product['source'] = name

    product['summary'] = d('h1').html()

    for i in d('div.col-md-8, div.col-sm-8, div.col-md-5, div.col-md-6, div.col-sm-5, div.col-sm-6').items('p, h3, h2'):
        i.remove('a, br, img')
        if i.parent().parent()('blockquote'):
            i = i.parent().parent()('blockquote')
            product['description'] += '<blockquote>'
            product['description'] += str(i('p'))
            product['description'] += u'<p align=right> ― <em>' + i('cite').html() + '</em></p>'
            product['description'] += '</blockquote>'
        elif i.html() and len(i.html()) > 0: # can't remove empty tags with :empty for some reason
            product['description'] += str(i)
            product['description'].replace('h2', 'h4')
            product['description'].replace('h3', 'h4')

    if name == "Fedora Workstation":
        product['logo'] = 'qrc:/logo_workstation'
    if name == "Fedora Server":
        product['logo'] = 'qrc:/logo_server'

    download = getDownload(url + "/download/")
    product['variants'] = download
    product['version'] = getRelease(download)
    if product['version'] == '23':
        product['releaseDate'] = '2015-11-03'

    return product

def getProducts(url='https://getfedora.org/'):
    d = pyquery.PyQuery(urlread(url))

    products = []

    for i in d('div.productitem').items('a'):
        productUrl = url
        if i.attr('href').startswith("../"):
            productUrl += i.attr('href')[3:]
        else:
            productUrl += i.attr('href')

        if not "cloud" in productUrl and not productUrl.endswith("download"):
            products.append(getProductDetails(productUrl))

    return products

def get_fedora_flavors():
    releases = []
    releases += getProducts('https://getfedora.org/')
    releases += [{'name': _('Custom OS...'),
                  'description': _('<p>Here you can choose a OS image from your hard drive to be written to your flash disk</p><p>Currently it is only supported to write raw disk images (.iso or .bin)</p>'),
                  'logo': 'qrc:/icon_folder',
                  'screenshots': [],
                  'summary': _('Pick a file from your drive(s)'),
                  'version': '',
                  'releaseDate': '',
                  'source': 'Local',
                  'variants': {'': dict(url='', sha256='', size=0)}}]
    releases += getSpins("http://spins.fedoraproject.org", "Spins")
    releases += getSpins("http://labs.fedoraproject.org", "Labs")
    return releases

# A backup list of releases, just in case we can't fetch them.
fedora_releases =  [{'description': u"<p>Fedora Workstation is a reliable, user-friendly, and powerful operating system for your laptop or desktop computer. It supports a wide range of developers, from hobbyists and students to professionals in corporate environments.</p>\n        <blockquote><p>&#8220;The plethora of tools provided by  Fedora allows me to get the job done.  It just works.&#8221;</p>\n              <p align=right> \u2015 <em>Christine Flood, JVM performance engineer</em></p></blockquote><h3>Sleek user interface</h3>\n\t      <p>Focus on your code in the GNOME 3 desktop environment. GNOME is built with developer feedback and minimizes distractions, so you can concentrate on what's important.</p>\n        <h3>Complete open source toolbox</h3>\n\t      <p>Skip the drag of trying to find or build the tools you need. With Fedora's complete set of open source languages, tools, and utilities, everything is a click or command line away. There's even project hosting and repositories like COPR to make your code and builds available quickly to the community.</p>\n        <h3>GNOME Boxes &amp; other virt tools</h3>\n\t      <p>Get virtual machines up and running quickly to test your code on multiple platforms using GNOME Boxes. Or dig into powerful, scriptable virtualization tools for even more control.</p>\n        <h3>Built-in Docker support</h3>\n\t      <p>Containerize your own apps, or deploy containerized apps out of the box on Fedora, using the latest technology like Docker.</p>\n        ",
  'logo': 'qrc:/logo_workstation',
  'name': 'Fedora Workstation',
  'releaseDate': '2015-11-03',
  'screenshots': [],
  'source': 'Fedora Workstation',
  'summary': "This is the Linux workstation you've been waiting for.",
  'variants': {'i686': {'sha256': '1f3fe28a51d0500ac19030b28e4dfb151d4a6368a9c25fb29ac9a3d29d47a838',
                        'size': 1395864371,
                        'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/23/Workstation/i386/iso/Fedora-Live-Workstation-i686-23-10.iso'},
               'x86_64': {'sha256': 'a91eca2492ac84909953ef27040f9b61d8525f7ec5e89f6430319f49f9f823fe',
                          'size': 1503238553,
                          'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/23/Workstation/x86_64/iso/Fedora-Live-Workstation-x86_64-23-10.iso'}},
  'version': '23'},
 {'description': u"<blockquote><p>&#8220;The simplicity introduced with rolekit and cockpit have made server deployments a breeze. What took me a few days on other operating systems took less than an hour with Fedora 23 Server. It just works.&#8221;</p>\n            <p align=right> \u2015 <em>Dan Mossor, Systems Engineer</em></p></blockquote><p>Fedora Server is a short-lifecycle, community-supported server operating system that enables seasoned system administrators experienced with any OS to make use of the very latest server-based technologies available in the open source community.</p>\n        <h3>Easy Administration</h3>\n  \t      <p>Manage your system simply with Cockpit's powerful, modern interface. View and monitor system performance and status, and deploy and manage container-based services.</p>\n        <h3>Server Roles</h3>\n\t        <p>There's no need to set up your server from scratch when you use server roles. Server roles plug into your Fedora Server system, providing a well-integrated service on top of the Fedora Server platform. Deploy and manage these prepared roles simply using the Rolekit tool.</p>\n        <h3>Database Services</h3>\n\t        <p>Fedora Server brings with it an enterprise-class, scalable database server powered by the open-source PostgreSQL project.</p>\n        <h3>Complete Enterprise Domain Solution</h3>\n\t      <p>Level up your Linux network with advanced identity management, DNS, certificate services, Windows(TM) domain integration throughout your environment with FreeIPA, the engine that drives Fedora Server's Domain Controller role.</p>\n        <blockquote><p>&#8220;The Docker Role for Fedora Server was simple and fast to install so that you can run your Docker images. This makes a great testbed for beginners and experts with docker so that they can develop their applications on the fly.&#8221;</p>\n            <p align=right> \u2015 <em>John Unland, Information Systems Student</em></p></blockquote>",
  'logo': 'qrc:/logo_server',
  'name': 'Fedora Server',
  'releaseDate': '2015-11-03',
  'screenshots': [],
  'source': 'Fedora Server',
  'summary': 'The latest technology. A stable foundation. Together, for your applications and services.',
  'variants': {'i386': {'sha256': 'aa2125b6351480ce82ace619925d897d0588195a3287ef74fb203b6eb34cbccf',
                        'size': 2254857830,
                        'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/23/Server/i386/iso/Fedora-Server-DVD-i386-23.iso'},
               'x86_64': {'sha256': '30758dc821d1530de427c9e35212bd79b058bd4282e64b7b34ae1a40c87c05ae',
                          'size': 2147483648,
                          'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/23/Server/x86_64/iso/Fedora-Server-DVD-x86_64-23.iso'}},
  'version': '23'},
 {'description': u'<p>Here you can choose a OS image from your hard drive to be written to your flash disk</p><p>Currently it is only supported to write raw disk images (.iso or .bin)</p>',
  'logo': 'qrc:/icon_folder',
  'name': u'Custom OS...',
  'releaseDate': '',
  'screenshots': [],
  'source': 'Local',
  'summary': u'Pick a file from your drive(s)',
  'variants': {'': {'sha256': '', 'size': 0, 'url': ''}},
  'version': ''},
 {'description': '',
  'logo': '',
  'name': 'Fedora Spins',
  'releaseDate': '',
  'screenshots': [],
  'source': '',
  'summary': 'Alternative desktops for Fedora',
  'variants': {},
  'version': ''},
 {'description': u'<p>The Fedora KDE Plasma Desktop Edition is a powerful Fedora-based operating system utilizing the KDE Plasma Desktop as the main user interface.</p><p>Fedora KDE Plasma Desktop comes with many pre-selected top quality applications that suit all modern desktop use cases - from online communication like web browsing, instant messaging and electronic mail correspondence, through multimedia and entertainment, to an advanced productivity suite, including office applications and enterprise grade personal information management.</p><p>All KDE applications are well integrated, with a similar look and feel and an easy to use interface, accompanied by an outstanding graphical appearance.</p>',
  'logo': 'qrc:/logo_plasma',
  'name': 'Fedora KDE Plasma Desktop',
  'releaseDate': '2015-11-03',
  'screenshots': ['http://spins.stg.fedoraproject.org/en/kde/../static/images/screenshots/screenshot-kde.jpg'],
  'source': 'Spins',
  'summary': 'A complete, modern desktop built using the KDE Plasma Desktop.',
  'variants': {'i686': {'sha256': '60f7e4efbe04cf89918df01e218042b698dccc5767d47208b9f46c6cd4ceb49b',
                        'size': 1288490188,
                        'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/23/Live/i386/Fedora-Live-KDE-i686-23-10.iso'},
               'x86_64': {'sha256': 'ef7e5ed9eee6dbcde1e0a4d69c76ce6fb552f75ccad879fa0f93031ceb950f27',
                          'size': 1288490188,
                          'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/23/Live/x86_64/Fedora-Live-KDE-x86_64-23-10.iso'}},
  'version': '23'},
 {'description': u'<p>The Fedora Xfce spin showcases the Xfce desktop, which aims to be fast and lightweight, while still being visually appealing and user friendly.</p><p>Fedora Xfce is a full-fledged desktop using the freedesktop.org standards.</p>',
  'logo': 'qrc:/logo_xfce',
  'name': 'Fedora Xfce Desktop',
  'releaseDate': '2015-11-03',
  'screenshots': ['http://spins.stg.fedoraproject.org/en/xfce/../static/images/screenshots/screenshot-xfce.jpg'],
  'source': 'Spins',
  'summary': 'A complete, well-integrated Xfce Desktop.',
  'variants': {'i686': {'sha256': '9111100e47742bd62a4b3ecaf79b985921601ac1d7616bb5ea0d924b4cfda8ba',
                        'size': 934281216,
                        'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/23/Live/i386/Fedora-Live-Xfce-i686-23-10.iso'},
               'x86_64': {'sha256': 'a24e48a604c81f8e3c3fbdd48a907d7168d0bc5310a0072f8b844aa799dd3365',
                          'size': 960495616,
                          'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/23/Live/x86_64/Fedora-Live-Xfce-x86_64-23-10.iso'}},
  'version': '23'},
 {'description': u'<p>LXDE, the "Lightweight X11 Desktop Environment", is an extremely fast, performant, and energy-saving desktop environment. It maintained by an international community of developers and comes with a beautiful interface, multi-language support, standard keyboard shortcuts and additional features like tabbed file browsing.</p><p>LXDE is not designed to be powerful and bloated, but to be usable and slim. A main goal of LXDE is to keep computer resource usage low. It is especially designed for computers with low hardware specifications like netbooks, mobile devices (e.g. MIDs) or older computers.</p>',
  'logo': 'qrc:/logo_lxde',
  'name': 'Fedora LXDE Desktop',
  'releaseDate': '2015-11-03',
  'screenshots': ['http://spins.stg.fedoraproject.org/en/lxde/../static/images/screenshots/screenshot-lxde.jpg'],
  'source': 'Spins',
  'summary': 'A light, fast, less-resource hungry desktop environment.',
  'variants': {'i686': {'sha256': '0298e4ef3f514911105d3cfaa29bb35f08bcc0319386de703b89a43c88eade15',
                        'size': 1010827264,
                        'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/23/Live/i386/Fedora-Live-LXDE-i686-23-10.iso'},
               'x86_64': {'sha256': '9b2acffef7ee8d8445fab427ef06afb0e888448241f761fc59aec59f53c7b3f0',
                          'size': 877658112,
                          'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/23/Live/x86_64/Fedora-Live-LXDE-x86_64-23-10.iso'}},
  'version': '23'},
 {'description': u'<p>The MATE Compiz spin bundles MATE Desktop with Compiz Fusion. MATE Desktop is a lightweight, powerful desktop designed with productivity and performance in mind. The default windows manager is Marco which is usable for all machines and VMs. Compiz Fusion is a beautiful 3D windowing manager with Emerald and GTK+ theming.</p><p>If you want a powerful, lightweight Fedora desktop with 3D eyecandy you should definitely try the MATE-Compiz spin.</p>',
  'logo': 'qrc:/logo_mate',
  'name': 'Fedora MATE-Compiz Desktop',
  'releaseDate': '2015-11-03',
  'screenshots': ['http://spins.stg.fedoraproject.org/en/mate-compiz/../static/images/screenshots/screenshot-matecompiz.jpg'],
  'source': 'Spins',
  'summary': 'A classic Fedora Desktop with an additional 3D Windows Manager.',
  'variants': {'i686': {'sha256': 'f33b7c0320796a907a471324b5934152371e6fc3d291fcb5e63b664e797ca2ed',
                        'size': 1288490188,
                        'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/23/Live/i386/Fedora-Live-MATE_Compiz-i686-23-10.iso'},
               'x86_64': {'sha256': '5cc5dd3b4c8dfa3b57cc9700404cb1d4036265691af7f28714456b5983d57737',
                          'size': 1395864371,
                          'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/23/Live/x86_64/Fedora-Live-MATE_Compiz-x86_64-23-10.iso'}},
  'version': '23'},
 {'description': u'<p>Cinnamon is a Linux desktop which provides advanced innovative features and a traditional user experience. The desktop layout is similar to Gnome 2. The underlying technology is forked from Gnome Shell. The emphasis is put on making users feel at home and providing them with an easy to use and comfortable desktop experience.</p><p>Cinnamon is a popular desktop alternative to Gnome 3 and this spin provides the option to quickly try and install this desktop.</p>',
  'logo': 'qrc:/logo_cinnamon',
  'name': 'Fedora Cinnamon Desktop',
  'releaseDate': '2015-11-03',
  'screenshots': ['http://spins.stg.fedoraproject.org/en/cinnamon/../static/images/screenshots/screenshot-cinnamon.jpg'],
  'source': 'Spins',
  'summary': 'A modern desktop featuring traditional Gnome user experience.',
  'variants': {'i686': {'sha256': '5bfe789ed8fbcbf6c22e1c30b8a38e373206303ff9a12b7f2dd108ade33473b8',
                        'size': 1288490188,
                        'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/23/Live/i386/Fedora-Live-Cinnamon-i686-23-10.iso'},
               'x86_64': {'sha256': '4585ff18d8f7b019f9f15119ecb6ee8ddeb947cba4c4d649d6689032ef57cca9',
                          'size': 1288490188,
                          'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/23/Live/x86_64/Fedora-Live-Cinnamon-x86_64-23-10.iso'}},
  'version': '23'},
 {'description': u'<p>Sugar on a Stick is a Fedora-based operating system featuring the award-winning Sugar Learning Platform and designed to fit on an ordinary USB thumbdrive ("stick").</p><p>Sugar sets aside the traditional \u201coffice-desktop\u201d metaphor, presenting a child-friendly graphical environment. Sugar automatically saves your progress to a "Journal" on your stick, so teachers and parents can easily pull up "all collaborative web browsing sessions done in the past week" or "papers written with Daniel and Sarah in the last 24 hours" with a simple query rather than memorizing complex file/folder structures. Applications in Sugar are known as Activities, some of which are described below.</p><p>It is now deployable for the cost of a stick rather than a laptop; students can take their Sugar on a Stick thumbdrive to any machine - at school, at home, at a library or community center - and boot their customized computing environment without touching the host machine\u2019s hard disk or existing system at all.</p>',
  'logo': 'qrc:/logo_soas',
  'name': 'Fedora SoaS Desktop',
  'releaseDate': '2015-11-03',
  'screenshots': ['http://spins.stg.fedoraproject.org/en/soas/../static/images/screenshots/screenshot-soas.jpg'],
  'source': 'Spins',
  'summary': 'Discover. Reflect. Share. Learn.',
  'variants': {'i686': {'sha256': 'f1cc96b9c07f182409e74b0346ffdafece15eddb91926637759fb3d3460ff128',
                        'size': 708837376,
                        'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/23/Live/i386/Fedora-Live-SoaS-i686-23-10.iso'},
               'x86_64': {'sha256': 'cdc364a5afdad91e615cf30aca8cd0c7ad9091e0d485bab4dcfc802a83600207',
                          'size': 732954624,
                          'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/23/Live/x86_64/Fedora-Live-SoaS-x86_64-23-10.iso'}},
  'version': '23'},
 {'description': '',
  'logo': '',
  'name': 'Fedora Labs',
  'releaseDate': '',
  'screenshots': [],
  'source': '',
  'summary': 'Functional bundles for Fedora',
  'variants': {},
  'version': ''},
 {'description': u'<p>Looking for a ready-to-go desktop environment brimming with free and open source multimedia production and publishing tools? Try the Design Suite, a Fedora Spin created by designers, for designers.</p><p>The Design Suite includes the favorite tools of the Fedora Design Team. These are the same programs we use to create all the artwork that you see within the Fedora Project, from desktop backgrounds to CD sleeves, web page designs, application interfaces, flyers, posters and more. From document publication to vector and bitmap editing or 3D modeling to photo management, the Design Suite has an application for you \u2014 and you can install thousands more from the Fedora universe of packages.</p>',
  'logo': 'qrc:/logo_design',
  'name': 'Fedora Design Suite',
  'releaseDate': '2015-11-03',
  'screenshots': [],
  'source': 'Labs',
  'summary': 'Visual design, multimedia production, and publishing suite of free and open source creative tools.',
  'variants': {'i686': {'sha256': '8cdc37d92a0c2322ad3789b2c9f7960311e85d0f3628b82fd530d54cf7c45110',
                        'size': 2040109465,
                        'url': 'https://download.fedoraproject.org/pub/alt/releases/23/Spins/i386/Fedora-Live-Design_suite-i686-23-10.iso'},
               'x86_64': {'sha256': 'beb5b9129a19d494064269d2b4be398f6724ff0128adc245d4e5414b4ea1196c',
                          'size': 1932735283,
                          'url': 'https://download.fedoraproject.org/pub/alt/releases/23/Spins/x86_64/Fedora-Live-Design_suite-x86_64-23-10.iso'}},
  'version': '23'},
 {'description': u"<p>The Fedora Games spin offers a perfect showcase of the best games available in Fedora. The included games span several genres, from first-person shooters to real-time and turn-based strategy games to puzzle games.</p><p>Not all the games available in Fedora are included on this spin, but trying out this spin will give you a fair impression of Fedora's ability to run great games.</p>",
  'logo': 'qrc:/logo_games',
  'name': 'Fedora Games',
  'releaseDate': '2015-11-03',
  'screenshots': [],
  'source': 'Labs',
  'summary': 'A collection and perfect show-case of the best games available in Fedora.',
  'variants': {'i686': {'sha256': 'fa9d4003094e85e2f667a7a065dbd1f59903ad61a3a3154aabc0db2ebe68093a',
                        'size': 3972844748,
                        'url': 'https://download.fedoraproject.org/pub/alt/releases/23/Spins/i386/Fedora-Live-Games-i686-23-10.iso'},
               'x86_64': {'sha256': '5b4a9264f176fb79e3e6de280ade23af80cda65112e8dc9cfc8c44fcd60b0eb4',
                          'size': 4187593113,
                          'url': 'https://download.fedoraproject.org/pub/alt/releases/23/Spins/x86_64/Fedora-Live-Games-x86_64-23-10.iso'}},
  'version': '23'},
 {'description': u'<p>The Fedora Robotics spin provides a wide variety of free and open robotics software packages. These range from hardware accessory libraries for the Hokuyo laser scanners or Katana robotic arm to software frameworks like Fawkes or Player and simulation environments such as Stage and RoboCup Soccer Simulation Server 2D/3D. It also provides a ready to use development environment for robotics including useful libraries such as OpenCV computer vision library, Festival text to speech system and MRPT.</p><p>The Robotics spin is targeted at people just discovering their interest in robotics as well as experienced roboticists. For the former we provide a readily usable simulation environment with an introductory hands-on demonstration, and for the latter we provide a full development environment, to be used immediately.</p>',
  'logo': 'qrc:/logo_robotics',
  'name': 'Fedora Robotics Suite',
  'releaseDate': '2015-11-03',
  'screenshots': [],
  'source': 'Labs',
  'summary': 'A wide variety of free and open robotics software packages for beginners and experts in robotics.',
  'variants': {'i686': {'sha256': 'c76a71ef18bedf07e6c41e6a26a740562121c32e32acd5200c255f3c47ada0a8',
                        'size': 2684354560,
                        'url': 'https://download.fedoraproject.org/pub/alt/releases/23/Spins/i386/Fedora-Live-Robotics-i686-23-10.iso'},
               'x86_64': {'sha256': '71008e7035cc4ac79da7166786450ac2d73df5dab2240070af8e52e81aab11ea',
                          'size': 2684354560,
                          'url': 'https://download.fedoraproject.org/pub/alt/releases/23/Spins/x86_64/Fedora-Live-Robotics-x86_64-23-10.iso'}},
  'version': '23'},
 {'description': u'<p>Wary of reinstalling all the essential tools for your scientific and numerical work? The answer is here. Fedora Scientific Spin brings together the most useful open source scientific and numerical tools atop the goodness of the KDE desktop environment.</p><p>Fedora Scientific currently ships with numerous applications and libraries. These range from libraries such as the GNU Scientific library, the SciPy libraries, tools like Octave and xfig to typesetting tools like Kile and graphics programs such as Inkscape. The current set of packages include an IDE, tools and libraries for programming in C, C++, Python, Java and R. Also included along with are libraries for parallel computing such as the OpenMPI and OpenMP. Tools for typesetting, writing and publishing are included.</p>',
  'logo': 'qrc:/logo_scientific',
  'name': 'Fedora Scientific',
  'releaseDate': '2015-11-03',
  'screenshots': [],
  'source': 'Labs',
  'summary': 'A bundle of open source scientific and numerical tools used in research.',
  'variants': {'i686': {'sha256': '72669c5fa57ab298d73cf545c88050977cdbaf8f2ee573e6146651cb4a156b53',
                        'size': 2791728742,
                        'url': 'https://download.fedoraproject.org/pub/alt/releases/23/Spins/i386/Fedora-Live-Scientific_KDE-i686-23-10.iso'},
               'x86_64': {'sha256': '255b73a16feb8b44cdf546338ce48a3085be858dfeccfca1df03b87ff7d57934',
                          'size': 2899102924,
                          'url': 'https://download.fedoraproject.org/pub/alt/releases/23/Spins/x86_64/Fedora-Live-Scientific_KDE-x86_64-23-10.iso'}},
  'version': '23'},
 {'description': u'<p>The Fedora Security Lab provides a safe test environment to work on security auditing, forensics, system rescue and teaching security testing methodologies in universities and other organizations.</p><p>The spin is maintained by a community of security testers and developers. It comes with the clean and fast Xfce Desktop Environment and a customized menu that provides all the instruments needed to follow a proper test path for security testing or to rescue a broken system. The Live image has been crafted to make it possible to install software while running, and if you are running it from a USB stick created with LiveUSB Creator using the overlay feature, you can install and update software and save your test results permanently.</p>',
  'logo': 'qrc:/logo_security',
  'name': 'Fedora Security Lab',
  'releaseDate': '2015-11-03',
  'screenshots': [],
  'source': 'Labs',
  'summary': 'A safe test environment to work on security auditing, forensics, system rescue and teaching security testing methodologies.',
  'variants': {'i686': {'sha256': '2a41ea039b6bfac18f6e45ca0d474f566fd4f70365ba6377dfaaf488564ffe98',
                        'size': 960495616,
                        'url': 'https://download.fedoraproject.org/pub/alt/releases/23/Spins/i386/Fedora-Live-Security-i686-23-10.iso'},
               'x86_64': {'sha256': 'fe712e118b72ac5727196a371dd4bf3472f84cc1b22a6c05d90af7a4cf3abd12',
                          'size': 985661440,
                          'url': 'https://download.fedoraproject.org/pub/alt/releases/23/Spins/x86_64/Fedora-Live-Security-x86_64-23-10.iso'}},
  'version': '23'}]


releases = fedora_releases

if __name__ == '__main__':
    import pprint
    pprint.pprint(get_fedora_flavors())
