# -*- coding: utf-8 -*-

import re
import traceback

from pyquery import pyquery

import grabber
from liveusb import _, LiveUSBError
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
        d = pyquery.PyQuery(grabber.urlread(baseurl))
    except LiveUSBError, e:
        return ''
    checksum = ''
    for i in d.items('a'):
        if 'CHECKSUM' in i.attr('href'):
            try:
                checksum = grabber.urlread(baseurl + '/' + i.attr('href'))
            except LiveUSBError, e:
                pass
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
    try:
        d = pyquery.PyQuery(grabber.urlread(url))
    except LiveUSBError, e:
        return None
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
    try:
        d = pyquery.PyQuery(grabber.urlread(url))
    except LiveUSBError, e:
        return None
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
    if not download:
        return None
    spin['variants'] = download
    spin['version'] = getRelease(download)
    if spin['version'] == '23':
        spin['releaseDate'] = '2015-11-03'
    if spin['version'] == '24':
        spin['releaseDate'] = '2016-06-21'

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
    try:
        d = pyquery.PyQuery(grabber.urlread(url))
    except LiveUSBError, e:
        return None
    spins = []

    for i in d('div').filter('.high').items('span'):
        spinUrl = url + i.siblings()('a').attr('href')
        spin = getSpinDetails(spinUrl, source)
        if not spin:
            continue
        spin['summary'] = i.html()
        spins.append(spin)

    return spins

def getProductDetails(url):
    d = pyquery.PyQuery(grabber.urlread(url))
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
    if product['version'] == '24':
        product['releaseDate'] = '2016-06-21'

    return product

def getProducts(url='https://getfedora.org/'):
    try:
        d = pyquery.PyQuery(grabber.urlread(url))
    except LiveUSBError, e:
        return None

    products = []

    for i in d('div.productitem').items('a'):
        productUrl = url
        if i.attr('href').startswith("../"):
            productUrl += i.attr('href')[3:]
        else:
            productUrl += i.attr('href')

        if not "cloud" in productUrl and not productUrl.endswith("download"):
            product = getProductDetails(productUrl)
            if product:
                products.append(product)

    return products

def get_fedora_flavors(store=True):
    r = []
    products = getProducts('https://getfedora.org/')
    spins = getSpins("http://spins.fedoraproject.org", "Spins")
    labs = getSpins("http://labs.fedoraproject.org", "Labs")

    if products:
        r += products
    r += [{'name': _('Custom OS...'),
                  'description': _('<p>Here you can choose a OS image from your hard drive to be written to your flash disk</p><p>Currently it is only supported to write raw disk images (.iso or .bin)</p>'),
                  'logo': 'qrc:/icon_folder',
                  'screenshots': [],
                  'summary': _('Pick a file from your drive(s)'),
                  'version': '',
                  'releaseDate': '',
                  'source': 'Local',
                  'variants': {'': dict(url='', sha256='', size=0)}}]
    if spins:
        r += spins
    if labs:
        r += labs

    if store and len(r) > 1:
        releases[:] = r

    return r

# A backup list of releases, just in case we can't fetch them.
fedora_releases =  [{'description': u"<p>Fedora Workstation is a reliable, user-friendly, and powerful operating system for your laptop or desktop computer. It supports a wide range of developers, from hobbyists and students to professionals in corporate environments.</p>\n        <blockquote><p>&#8220;The plethora of tools provided by  Fedora allows me to get the job done.  It just works.&#8221;</p>\n              <p align=right> \u2015 <em>Christine Flood, JVM performance engineer</em></p></blockquote><h3>Sleek user interface</h3>\n\t      <p>Focus on your code in the GNOME 3 desktop environment. GNOME is built with developer feedback and minimizes distractions, so you can concentrate on what's important.</p>\n        <h3>Complete open source toolbox</h3>\n\t      <p>Skip the drag of trying to find or build the tools you need. With Fedora's complete set of open source languages, tools, and utilities, everything is a click or command line away. There's even project hosting and repositories like COPR to make your code and builds available quickly to the community.</p>\n        <h3>GNOME Boxes &amp; other virt tools</h3>\n\t      <p>Get virtual machines up and running quickly to test your code on multiple platforms using GNOME Boxes. Or dig into powerful, scriptable virtualization tools for even more control.</p>\n        <h3>Built-in Docker support</h3>\n\t      <p>Containerize your own apps, or deploy containerized apps out of the box on Fedora, using the latest technology like Docker.</p>\n        ",
  'logo': 'qrc:/logo_workstation',
  'name': 'Fedora Workstation',
  'releaseDate': '2016-06-21',
  'screenshots': [],
  'source': 'Fedora Workstation',
  'summary': "This is the Linux workstation you've been waiting for.",
  'variants': {'i386': {'sha256': '',
                        'size': 1717986918,
                        'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/24/Workstation/i386/iso/Fedora-Workstation-Live-i386-24-1.2.iso'},
               'x86_64': {'sha256': '',
                          'size': 1503238553,
                          'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/24/Workstation/x86_64/iso/Fedora-Workstation-Live-x86_64-24-1.2.iso'}},
  'version': '24'},
 {'description': u"<blockquote><p>&#8220;The simplicity introduced with rolekit and cockpit have made server deployments a breeze. What took me a few days on other operating systems took less than an hour with Fedora 24 Server. It just works.&#8221;</p>\n            <p align=right> \u2015 <em>Dan Mossor, Systems Engineer</em></p></blockquote><p>Fedora Server is a short-lifecycle, community-supported server operating system that enables seasoned system administrators experienced with any OS to make use of the very latest server-based technologies available in the open source community.</p>\n        <h3>Easy Administration</h3>\n  \t      <p>Manage your system simply with Cockpit's powerful, modern interface. View and monitor system performance and status, and deploy and manage container-based services.</p>\n        <h3>Server Roles</h3>\n\t        <p>There's no need to set up your server from scratch when you use server roles. Server roles plug into your Fedora Server system, providing a well-integrated service on top of the Fedora Server platform. Deploy and manage these prepared roles simply using the Rolekit tool.</p>\n        <h3>Database Services</h3>\n\t        <p>Fedora Server brings with it an enterprise-class, scalable database server powered by the open-source PostgreSQL project.</p>\n        <h3>Complete Enterprise Domain Solution</h3>\n\t      <p>Level up your Linux network with advanced identity management, DNS, certificate services, Windows(TM) domain integration throughout your environment with FreeIPA, the engine that drives Fedora Server's Domain Controller role.</p>\n        <blockquote><p>&#8220;The Docker Role for Fedora Server was simple and fast to install so that you can run your Docker images. This makes a great testbed for beginners and experts with docker so that they can develop their applications on the fly.&#8221;</p>\n            <p align=right> \u2015 <em>John Unland, Information Systems Student</em></p></blockquote>",
  'logo': 'qrc:/logo_server',
  'name': 'Fedora Server',
  'releaseDate': '2016-06-21',
  'screenshots': [],
  'source': 'Fedora Server',
  'summary': 'The latest technology. A stable foundation. Together, for your applications and services.',
  'variants': {'x86_64': {'sha256': '1c0971d4c1a37bb06ec603ed3ded0af79e22069499443bb2d47e501c9ef42ae8',
                          'size': 1825361100,
                          'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/24/Server/x86_64/iso/Fedora-Server-dvd-x86_64-24-1.2.iso'}},
  'version': '24'},
 {'description': u'<p>Here you can choose a OS image from your hard drive to be written to your flash disk</p><p>Currently it is only supported to write raw disk images (.iso or .bin)</p>',
  'logo': 'qrc:/icon_folder',
  'name': u'Custom OS...',
  'releaseDate': '',
  'screenshots': [],
  'source': 'Local',
  'summary': u'Pick a file from your drive(s)',
  'variants': {'': {'sha256': '', 'size': 0, 'url': ''}},
  'version': ''},
 {'description': u'<p>The Fedora KDE Plasma Desktop Edition is a powerful Fedora-based operating system utilizing the KDE Plasma Desktop as the main user interface.</p><p>Fedora KDE Plasma Desktop comes with many pre-selected top quality applications that suit all modern desktop use cases - from online communication like web browsing, instant messaging and electronic mail correspondence, through multimedia and entertainment, to an advanced productivity suite, including office applications and enterprise grade personal information management.</p><p>All KDE applications are well integrated, with a similar look and feel and an easy to use interface, accompanied by an outstanding graphical appearance.</p>',
  'logo': 'qrc:/logo_plasma',
  'name': 'Fedora KDE Plasma Desktop',
  'releaseDate': '2016-06-21',
  'screenshots': ['http://spins.fedoraproject.org/en/kde/../static/images/screenshots/screenshot-kde.jpg'],
  'source': 'Spins',
  'summary': 'A complete, modern desktop built using the KDE Plasma Desktop.',
  'variants': {'i386': {'sha256': '',
                        'size': 1288490188,
                        'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/24/Live/i386/Fedora-KDE-Live-i386-24-1.2.iso'},
               'x86_64': {'sha256': '',
                          'size': 1288490188,
                          'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/24/Live/x86_64/Fedora-KDE-Live-x86_64-24-1.2.iso'}},
  'version': '24'},
 {'description': u'<p>The Fedora Xfce spin showcases the Xfce desktop, which aims to be fast and lightweight, while still being visually appealing and user friendly.</p><p>Fedora Xfce is a full-fledged desktop using the freedesktop.org standards.</p>',
  'logo': 'qrc:/logo_xfce',
  'name': 'Fedora Xfce Desktop',
  'releaseDate': '2016-06-21',
  'screenshots': ['http://spins.fedoraproject.org/en/xfce/../static/images/screenshots/screenshot-xfce.jpg'],
  'source': 'Spins',
  'summary': 'A complete, well-integrated Xfce Desktop.',
  'variants': {'i386': {'sha256': '',
                        'size': 934281216,
                        'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/24/Live/i386/Fedora-Xfce-Live-i386-24-1.2.iso'},
               'x86_64': {'sha256': '',
                          'size': 960495616,
                          'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/24/Live/x86_64/Fedora-Xfce-Live-x86_64-24-1.2.iso'}},
  'version': '24'},
 {'description': u'<p>LXDE, the "Lightweight X11 Desktop Environment", is an extremely fast, performant, and energy-saving desktop environment. It maintained by an international community of developers and comes with a beautiful interface, multi-language support, standard keyboard shortcuts and additional features like tabbed file browsing.</p><p>LXDE is not designed to be powerful and bloated, but to be usable and slim. A main goal of LXDE is to keep computer resource usage low. It is especially designed for computers with low hardware specifications like netbooks, mobile devices (e.g. MIDs) or older computers.</p>',
  'logo': 'qrc:/logo_lxde',
  'name': 'Fedora LXDE Desktop',
  'releaseDate': '2016-06-21',
  'screenshots': ['http://spins.fedoraproject.org/en/lxde/../static/images/screenshots/screenshot-lxde.jpg'],
  'source': 'Spins',
  'summary': 'A light, fast, less-resource hungry desktop environment.',
  'variants': {'i386': {'sha256': '',
                        'size': 1010827264,
                        'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/24/Live/i386/Fedora-LXDE-Live-i386-24-1.2.iso'},
               'x86_64': {'sha256': '',
                          'size': 877658112,
                          'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/24/Live/x86_64/Fedora-LXDE-Live-x86_64-24-1.2.iso'}},
  'version': '24'},
 {'description': u'<p>The MATE Compiz spin bundles MATE Desktop with Compiz Fusion. MATE Desktop is a lightweight, powerful desktop designed with productivity and performance in mind. The default windows manager is Marco which is usable for all machines and VMs. Compiz Fusion is a beautiful 3D windowing manager with Emerald and GTK+ theming.</p><p>If you want a powerful, lightweight Fedora desktop with 3D eyecandy you should definitely try the MATE-Compiz spin.</p>',
  'logo': 'qrc:/logo_mate',
  'name': 'Fedora MATE-Compiz Desktop',
  'releaseDate': '2016-06-21',
  'screenshots': ['http://spins.fedoraproject.org/en/mate-compiz/../static/images/screenshots/screenshot-matecompiz.jpg'],
  'source': 'Spins',
  'summary': 'A classic Fedora Desktop with an additional 3D Windows Manager.',
  'variants': {'i386': {'sha256': '',
                        'size': 1288490188,
                        'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/24/Live/i386/Fedora-MATE_Compiz-Live-i386-24-1.2.iso'},
               'x86_64': {'sha256': '',
                          'size': 1395864371,
                          'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/24/Live/x86_64/Fedora-MATE_Compiz-Live-x86_64-24-1.2.iso'}},
  'version': '24'},
 {'description': u'<p>Cinnamon is a Linux desktop which provides advanced innovative features and a traditional user experience. The desktop layout is similar to Gnome 2. The underlying technology is forked from Gnome Shell. The emphasis is put on making users feel at home and providing them with an easy to use and comfortable desktop experience.</p><p>Cinnamon is a popular desktop alternative to Gnome 3 and this spin provides the option to quickly try and install this desktop.</p>',
  'logo': 'qrc:/logo_cinnamon',
  'name': 'Fedora Cinnamon Desktop',
  'releaseDate': '2016-06-21',
  'screenshots': ['http://spins.fedoraproject.org/en/cinnamon/../static/images/screenshots/screenshot-cinnamon.jpg'],
  'source': 'Spins',
  'summary': 'A modern desktop featuring traditional Gnome user experience.',
  'variants': {'i386': {'sha256': '',
                        'size': 1288490188,
                        'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/24/Live/i386/Fedora-Cinnamon-Live-i386-24-1.2.iso'},
               'x86_64': {'sha256': '',
                          'size': 1288490188,
                          'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/24/Live/x86_64/Fedora-Cinnamon-Live-x86_64-24-1.2.iso'}},
  'version': '24'},
 {'description': u'<p>Sugar on a Stick is a Fedora-based operating system featuring the award-winning Sugar Learning Platform and designed to fit on an ordinary USB thumbdrive ("stick").</p><p>Sugar sets aside the traditional \u201coffice-desktop\u201d metaphor, presenting a child-friendly graphical environment. Sugar automatically saves your progress to a "Journal" on your stick, so teachers and parents can easily pull up "all collaborative web browsing sessions done in the past week" or "papers written with Daniel and Sarah in the last 24 hours" with a simple query rather than memorizing complex file/folder structures. Applications in Sugar are known as Activities, some of which are described below.</p><p>It is now deployable for the cost of a stick rather than a laptop; students can take their Sugar on a Stick thumbdrive to any machine - at school, at home, at a library or community center - and boot their customized computing environment without touching the host machine\u2019s hard disk or existing system at all.</p>',
  'logo': 'qrc:/logo_soas',
  'name': 'Fedora SoaS Desktop',
  'releaseDate': '2016-06-21',
  'screenshots': ['http://spins.fedoraproject.org/en/soas/../static/images/screenshots/screenshot-soas.jpg'],
  'source': 'Spins',
  'summary': 'Discover. Reflect. Share. Learn.',
  'variants': {'i386': {'sha256': '2af7c621681c3f4978e71a25bfd608fa66d2b441db51806b9ab639901c8eec58',
                        'size': 708837376,
                        'url': 'http://dl.fedoraproject.org/pub/alt/unofficial/releases/24/i386/Fedora-SoaS-Live-i386-24-20160614.n.0.iso'},
               'x86_64': {'sha256': 'ba1dbd4bac36660f8f5b6ef9acaa18bcfb117413bc2b557b05a876778f4fa777',
                          'size': 732954624,
                          'url': 'http://dl.fedoraproject.org/pub/alt/unofficial/releases/24/x86_64/Fedora-SoaS-Live-x86_64-24-20160614.n.0.iso'}},
  'version': '24'},
 {'description': u'<p>Looking for a ready-to-go desktop environment brimming with free and open source multimedia production and publishing tools? Try the Design Suite, a Fedora Spin created by designers, for designers.</p><p>The Design Suite includes the favorite tools of the Fedora Design Team. These are the same programs we use to create all the artwork that you see within the Fedora Project, from desktop backgrounds to CD sleeves, web page designs, application interfaces, flyers, posters and more. From document publication to vector and bitmap editing or 3D modeling to photo management, the Design Suite has an application for you \u2014 and you can install thousands more from the Fedora universe of packages.</p>',
  'logo': 'qrc:/logo_design',
  'name': 'Fedora Design Suite',
  'releaseDate': '2016-06-21',
  'screenshots': [],
  'source': 'Labs',
  'summary': 'Visual design, multimedia production, and publishing suite of free and open source creative tools.',
  'variants': {'i386': {'sha256': '77ac8c0ec235604ea2a49ad475356d243636f460410038879504fc82665c1651',
                        'size': 2040109465,
                        'url': 'http://dl.fedoraproject.org/pub/alt/unofficial/releases/24/i386/Fedora-Design_suite-Live-i386-24-20160614.n.0.iso'},
               'x86_64': {'sha256': 'd9a44a18e7433e8d523fa38d7c0f71199b5866af57d17f3c1e433cdd098373cd',
                          'size': 1932735283,
                          'url': 'http://dl.fedoraproject.org/pub/alt/unofficial/releases/24/x86_64/Fedora-Design_suite-Live-x86_64-24-20160614.n.0.iso'}},
  'version': '24'},
 {'description': u"<p>The Fedora Games spin offers a perfect showcase of the best games available in Fedora. The included games span several genres, from first-person shooters to real-time and turn-based strategy games to puzzle games.</p><p>Not all the games available in Fedora are included on this spin, but trying out this spin will give you a fair impression of Fedora's ability to run great games.</p>",
  'logo': 'qrc:/logo_games',
  'name': 'Fedora Games',
  'releaseDate': '2016-06-21',
  'screenshots': [],
  'source': 'Labs',
  'summary': 'For audio enthusiasts and musicians who want to create, edit and produce audio and music on Linux.',
  'variants': {'i386': {'sha256': '',
                        'size': 4080218931,
                        'url': 'https://download.fedoraproject.org/pub/alt/releases/24/Spins/i386/Fedora-Games-Live-i386-24-1.2.iso'},
               'x86_64': {'sha256': '',
                          'size': 3865470566,
                          'url': 'https://download.fedoraproject.org/pub/alt/releases/24/Spins/x86_64/Fedora-Games-Live-x86_64-24-1.2.iso'}},
  'version': '24'},
 {'description': u'<p>The Fedora Robotics spin provides a wide variety of free and open robotics software packages. These range from hardware accessory libraries for the Hokuyo laser scanners or Katana robotic arm to software frameworks like Fawkes or Player and simulation environments such as Stage and RoboCup Soccer Simulation Server 2D/3D. It also provides a ready to use development environment for robotics including useful libraries such as OpenCV computer vision library, Festival text to speech system and MRPT.</p><p>The Robotics spin is targeted at people just discovering their interest in robotics as well as experienced roboticists. For the former we provide a readily usable simulation environment with an introductory hands-on demonstration, and for the latter we provide a full development environment, to be used immediately.</p>',
  'logo': 'qrc:/logo_robotics',
  'name': 'Fedora Robotics Suite',
  'releaseDate': '2016-06-21',
  'screenshots': [],
  'source': 'Labs',
  'summary': 'A wide variety of free and open robotics software packages for beginners and experts in robotics.',
  'variants': {'i386': {'sha256': '',
                        'size': 2899102924,
                        'url': 'https://download.fedoraproject.org/pub/alt/releases/24/Spins/i386/Fedora-Robotics-Live-i386-24-1.2.iso'},
               'x86_64': {'sha256': '',
                          'size': 2576980377,
                          'url': 'https://download.fedoraproject.org/pub/alt/releases/24/Spins/x86_64/Fedora-Robotics-Live-x86_64-24-1.2.iso'}},
  'version': '24'},
 {'description': u'<p>Wary of reinstalling all the essential tools for your scientific and numerical work? The answer is here. Fedora Scientific Spin brings together the most useful open source scientific and numerical tools atop the goodness of the KDE desktop environment.</p><p>Fedora Scientific currently ships with numerous applications and libraries. These range from libraries such as the GNU Scientific library, the SciPy libraries, tools like Octave and xfig to typesetting tools like Kile and graphics programs such as Inkscape. The current set of packages include an IDE, tools and libraries for programming in C, C++, Python, Java and R. Also included along with are libraries for parallel computing such as the OpenMPI and OpenMP. Tools for typesetting, writing and publishing are included.</p>',
  'logo': 'qrc:/logo_scientific',
  'name': 'Fedora Scientific',
  'releaseDate': '2016-06-21',
  'screenshots': [],
  'source': 'Labs',
  'summary': 'A bundle of open source scientific and numerical tools used in research.',
  'variants': {'i386': {'sha256': '',
                        'size': 3435973836,
                        'url': 'https://download.fedoraproject.org/pub/alt/releases/24/Spins/i386/Fedora-Scientific_KDE-Live-i386-24-1.2.iso'},
               'x86_64': {'sha256': '',
                          'size': 3113851289,
                          'url': 'https://download.fedoraproject.org/pub/alt/releases/24/Spins/x86_64/Fedora-Scientific_KDE-Live-x86_64-24-1.2.iso'}},
  'version': '24'},
 {'description': u'<p>The Fedora Security Lab provides a safe test environment to work on security auditing, forensics, system rescue and teaching security testing methodologies in universities and other organizations.</p><p>The spin is maintained by a community of security testers and developers. It comes with the clean and fast Xfce Desktop Environment and a customized menu that provides all the instruments needed to follow a proper test path for security testing or to rescue a broken system. The Live image has been crafted to make it possible to install software while running, and if you are running it from a USB stick created with LiveUSB Creator using the overlay feature, you can install and update software and save your test results permanently.</p>',
  'logo': 'qrc:/logo_security',
  'name': 'Fedora Security Lab',
  'releaseDate': '2016-06-21',
  'screenshots': [],
  'source': 'Labs',
  'summary': 'A safe test environment to work on security auditing, forensics, system rescue and teaching security testing methodologies.',
  'variants': {'i386': {'sha256': '',
                        'size': 1288490188,
                        'url': 'https://download.fedoraproject.org/pub/alt/releases/24/Spins/i386/Fedora-Security-Live-i386-24-1.2.iso'},
               'x86_64': {'sha256': '',
                          'size': 1181116006,
                          'url': 'https://download.fedoraproject.org/pub/alt/releases/24/Spins/x86_64/Fedora-Security-Live-x86_64-24-1.2.iso'}},
  'version': '24'}]


releases = fedora_releases

if __name__ == '__main__':
    import pprint
    pprint.pprint(get_fedora_flavors(False))
