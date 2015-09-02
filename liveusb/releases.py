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

def getRelease(url):
    return url.split('/')[-1].split('.')[0].split('-')[4]

def getSHA(url):
    baseurl = '/'.join(url.split('/')[:-1])
    filename = url.split('/')[-1]
    d = pyquery.PyQuery(urlread(baseurl))
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
        'releaseDate': '',
        'logo': 'qrc:/logo-fedora.svg',
        'screenshots': [],
        'source': '',
        'variants': {'': dict(
            url='',
            sha256='',
            size=0
        )}
    }
    spin['source'] = source

    spin['name'] = 'Fedora ' + d('title').html().strip()
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
    #spin['release'] = getRelease(download)

    if 'KDE Plasma' in spin['name']:
        spin['logo'] = 'qrc:/kde_icon.png'
    if 'Xfce' in spin['name']:
        spin['logo'] = 'qrc:/xfce_icon.png'
    if 'LXDE' in spin['name']:
        spin['logo'] = 'qrc:/lxde_icon.png'
    if 'MATE' in spin['name']:
        spin['logo'] = 'qrc:/mate_icon.png'
    if 'SoaS' in spin['name']:
        spin['logo'] = 'qrc:/soas_icon.png'

    if 'Astronomy' in spin['name']:
        spin['logo'] = 'qrc:/astronomy_icon_grey.png'
    if 'Design' in spin['name']:
        spin['logo'] = 'qrc:/design-suite_icon_grey.png'
    if 'Games' in spin['name']:
        spin['logo'] = 'qrc:/games_icon_grey.png'
    if 'Jam' in spin['name']:
        spin['logo'] = 'qrc:/jam_icon_grey.png'
    if 'Robotics' in spin['name']:
        spin['logo'] = 'qrc:/robotics-suite_icon_grey.png'
    if 'Scientific' in spin['name']:
        spin['logo'] = 'qrc:/scientific_icon_grey.png'
    if 'Security' in spin['name']:
        spin['logo'] = 'qrc:/security-lab_icon_grey.png'

    return spin

def getSpins(url, source):
    d = pyquery.PyQuery(urlread(url))
    spins = []

    if source == 'Spins':
        spins.append({'releaseDate': '', 'source': '', 'name': 'Fedora ' + source, 'logo': '', 'description': '', 'screenshots': '', 'variants': {}, 'summary': 'Alternative desktops for Fedora'})
    elif source == 'Labs':
        spins.append({'releaseDate': '', 'source': '', 'name': 'Fedora ' + source, 'logo': '', 'description': '', 'screenshots': '', 'variants': {}, 'summary': 'Functional bundles for Fedora'})

    for i in d('div').filter('.high').items('span'):
        spinUrl = url + i.siblings()('a').attr('href')
        spin = getSpinDetails(spinUrl, source)
        spin['summary'] = i.html()
        spins.append(spin)

    return spins

def getProductDetails(url, name):
    d = pyquery.PyQuery(urlread(url))
    product = {
        'name': '',
        'summary': '',
        'description': '',
        'releaseDate': '',
        'logo': 'qrc:/logo-fedora.svg',
        'screenshots': [],
        'source': '',
        'variants': {'': dict(
            url='',
            sha256='',
            size=0
        )}
    }
    product['name'] = name
    product['source'] = name

    product['summary'] = d('h1').html()

    for i in d('div.col-md-8, div.col-sm-8, div.col-md-5, div.col-md-6, div.col-sm-5, div.col-sm-6').items('p, h3, h2'):
        i.remove('a, br, img')
        if i.parent().parent()('blockquote'):
            i = i.parent().parent()('blockquote')
            product['description'] += '<blockquote>'
            product['description'] += str(i('p'))
            product['description'] += '<p align=right> ― <em>' + i('cite').html() + '</em></p>'
            product['description'] += '</blockquote>'
        elif i.html() and len(i.html()) > 0: # can't remove empty tags with :empty for some reason
            product['description'] += str(i)
            product['description'].replace('h2', 'h4')
            product['description'].replace('h3', 'h4')

    if name == "Workstation":
        product['name'] = 'Fedora Workstation'
        product['logo'] = 'qrc:/logo-color-workstation.png'
    if name == "Cloud":
        product['name'] = 'Fedora Cloud'
        product['logo'] = 'qrc:/logo-color-cloud.png'
    if name == "Server":
        product['name'] = 'Fedora Server'
        product['logo'] = 'qrc:/logo-color-server.png'

    download = getDownload(url + "/download")
    product['variants'] = download
    #product['release'] = getRelease(download)

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
        productName = i('h4').html()

        if productName != "Cloud":
            products.append(getProductDetails(productUrl, productName))

    return products

def get_fedora_flavors():
    releases = [{'name': _('Custom OS...'),
              'description': _('<p>Here you can choose a OS image from your hard drive to be written to your flash disk</p><p>Currently it is only supported to write raw disk images (.iso or .bin)</p>'),
              'logo': 'qrc:/icon-folder.svg',
              'screenshots': [],
              'summary': _('Pick a file from your drive(s)'),
              'releaseDate': '',
              'source': 'Local',
              'variants': {'': dict(url='', sha256='', size=0)}}]
    releases += getProducts('https://getfedora.org/')
    releases += getSpins("http://spins.fedoraproject.org", "Spins")
    releases += getSpins("http://labs.fedoraproject.org", "Labs")
    return releases

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
                    #print(arch_url)
                    try:
                        files = urlread(arch_url)
                    except URLGrabError:
                        continue
                    for link in re.findall(r'<a href="(.*)">', files):
                        if link.endswith('-CHECKSUM'):
                            #print('Reading %s' % arch_url + link)
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
{'releaseDate': '', 'source': 'Local', 'name': u'Custom OS...', 'logo': 'qrc:/icon-folder.svg', 'variants': {'': {'url': '', 'sha256': '', 'size': 0}}, 'summary': u'Pick a file from your drive(s)', 'screenshots': [], 'description': u'Here you can choose a OS image from your hard drive to be written to your flash disk'},
{'releaseDate': '', 'source': 'Workstation', 'name': 'Fedora Workstation', 'logo': 'qrc:/logo-color-workstation.png', 'description': "<p>Fedora Workstation is a reliable, user-friendly, and powerful operating system for your laptop or desktop computer. It supports a wide range of developers, from hobbyists and students to professionals in corporate environments.</p>\n        <blockquote><p>&#8220;The plethora of tools provided by  Fedora allows me to get the job done.  It just works.&#8221;</p>\n              <p align=right> \xe2\x80\x95 <em>Christine Flood, JVM performance engineer</em></p></blockquote><h3>Sleek user interface</h3>\n\t      <p>Focus on your code in the GNOME 3 desktop environment. GNOME is built with developer feedback and minimizes distractions, so you can concentrate on what's important.</p>\n        <h3>Complete open source toolbox</h3>\n\t      <p>Skip the drag of trying to find or build the tools you need. With Fedora's complete set of open source languages, tools, and utilities, everything is a click or command line away. There's even project hosting and repositories like COPR to make your code and builds available quickly to the community.</p>\n        <h3>GNOME Boxes &amp; other virt tools</h3>\n\t      <p>Get virtual machines up and running quickly to test your code on multiple platforms using GNOME Boxes. Or dig into powerful, scriptable virtualization tools for even more control.</p>\n        <h3>Built-in Docker support</h3>\n\t      <p>Containerize your own apps, or deploy containerized apps out of the box on Fedora, using the latest technology like Docker.</p>\n        ", 'screenshots': [], 'variants': {'x86_64': {'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/22/Workstation/x86_64/iso/Fedora-Live-Workstation-x86_64-22-3.iso', 'sha256': '615abfc89709a46a078dd1d39638019aa66f62b0ff8325334f1af100551bb6cf', 'size': 1395864371}, 'i686': {'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/22/Workstation/i386/iso/Fedora-Live-Workstation-i686-22-3.iso', 'sha256': '6e4c47b582ece2b431ee95d6f453945d11e28c712f7619b178cb31979138f884', 'size': 1395864371}}, 'summary': "This is the Linux workstation you've been waiting for."},
{'releaseDate': '', 'source': 'Server', 'name': 'Fedora Server', 'logo': 'qrc:/logo-color-server.png', 'description': "<blockquote><p>&#8220;The simplicity introduced with rolekit and cockpit have made server deployments a breeze. What took me a few days on other operating systems took less than an hour with Fedora 22 Server. It just works.&#8221;</p>\n            <p align=right> \xe2\x80\x95 <em>Dan Mossor, Systems Engineer</em></p></blockquote><p>Fedora Server is a powerful, flexible operating system that includes the best and latest datacenter technologies. It puts you in control of all your infrastructure and services.</p>\n        <h3>Cockpit</h3>\n\t      <p>Manage your system easily with Cockpit's powerful, modern interface. View and monitor system performance and status, and deploy and manage container-based services.</p>\n        <h3>Server Roles and Rolekit</h3>\n\t        <p>There's no need to set up your server from scratch when you use server roles. Server roles plug into your Fedora Server system, providing a well-integrated service on top of the Fedora Server platform. Deploy and manage these prepared roles simply using the Rolekit tool.</p>\n        <h3>OpenLMI tools</h3>\n\t        <p>Manage a wide variety of system parameters with OpenLMI. Simplify administration using its unified command set and powerful Python scripting interface.</p>\n        <h3>FreeIPA identity management</h3>\n\t      <p>Level up your Linux network with advanced identity management. Manage users, systems, and policy throughout your environment with FreeIPA, the engine that drives Fedora Server's Domain Controller role.</p>\n        <blockquote><p>&#8220;The Docker Role for Fedora Server was simple and fast to install so that you can run your Docker images. This makes a great testbed for beginners and experts with docker so that they can develop their applications on the fly.&#8221;</p>\n            <p align=right> \xe2\x80\x95 <em>John Unland, Information Systems Student</em></p></blockquote>", 'screenshots': [], 'variants': {'x86_64': {'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/22/Server/x86_64/iso/Fedora-Server-DVD-x86_64-22.iso', 'sha256': 'b2acfa7c7c6b5d2f51d3337600c2e52eeaa1a1084991181c28ca30343e52e0df', 'size': 2254857830}, 'i386': {'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/22/Server/i386/iso/Fedora-Server-DVD-i386-22.iso', 'sha256': '5e3dfdff30667f3339d8b4e6ac0651c2e00c9417987848bef772cb92dbc823a5', 'size': 2362232012}}, 'summary': 'The latest technology. A stable foundation. Together, for your applications and services.'},
{'releaseDate': '', 'source': '', 'name': 'Fedora Spins', 'logo': '', 'description': '', 'screenshots': '', 'variants': {'x86_64': {}, 'i686': {}, 'armv7hl': {}}, 'summary': 'Alternative desktops for Fedora'},
{'releaseDate': '', 'source': 'Spins', 'name': 'Fedora KDE Plasma Desktop', 'logo': 'qrc:/kde_icon.png', 'description': u'<p>The Fedora KDE Plasma Desktop Edition is a powerful Fedora-based operating system utilizing the KDE Plasma Desktop as the main user interface.</p><p>Fedora KDE Plasma Desktop comes with many pre-selected top quality applications that suit all modern desktop use cases - from online communication like web browsing, instant messaging and electronic mail correspondence, through multimedia and entertainment, to an advanced productivity suite, including office applications and enterprise grade personal information management.</p><p>All KDE applications are well integrated, with a similar look and feel and an easy to use interface, accompanied by an outstanding graphical appearance.</p>', 'screenshots': ['http://spins.fedoraproject.org/en/kde/../static/images/screenshots/screenshot-kde.jpg'], 'variants': {'x86_64': {'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/22/Live/x86_64/Fedora-Live-KDE-x86_64-22-3.iso', 'sha256': '0ccfbe7a2233cff2496aee037e3320471eb4de42ada2e27018cf5ac7adc14fdd', 'size': 1181116006}, 'i686': {'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/22/Live/i386/Fedora-Live-KDE-i686-22-3.iso', 'sha256': 'de9b7f049b3c7c10101537e26f3ac9392ca0e9846c3e6bfd63d23f9e7ba8612d', 'size': 1181116006}}, 'summary': 'A complete, modern desktop built using the KDE Plasma Desktop.'},
{'releaseDate': '', 'source': 'Spins', 'name': 'Fedora Xfce Desktop', 'logo': 'qrc:/xfce_icon.png', 'description': u'<p>The Fedora Xfce spin showcases the Xfce desktop, which aims to be fast and lightweight, while still being visually appealing and user friendly.</p><p>Fedora Xfce is a full-fledged desktop using the freedesktop.org standard.</p>', 'screenshots': ['http://spins.fedoraproject.org/en/xfce/../static/images/screenshots/screenshot-xfce.jpg'], 'variants': {'x86_64': {'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/22/Live/x86_64/Fedora-Live-Xfce-x86_64-22-3.iso', 'sha256': '08f1c79845b8e6a357aeeba42c7719db0d088d8dbf2df078b3202d2392b18949', 'size': 1007681536}, 'i686': {'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/22/Live/i386/Fedora-Live-Xfce-i686-22-3.iso', 'sha256': '4b76fe7db8ee2ad24499e84abfa6830b4f75f45b5772cfcc905ea928cb6852ae', 'size': 869269504}}, 'summary': 'A complete, well-integrated Xfce Desktop.'},
{'releaseDate': '', 'source': 'Spins', 'name': 'Fedora LXDE Desktop', 'logo': 'qrc:/lxde_icon.png', 'description': u'<p>LXDE, the "Lightweight X11 Desktop Environment", is an extremely fast, performant, and energy-saving desktop environment. It maintained by an international community of developers and comes with a beautiful interface, multi-language support, standard keyboard shortcuts and additional features like tabbed file browsing.</p><p>LXDE is not designed to be powerful and bloated, but to be usable and slim. A main goal of LXDE is to keep computer resource usage low. It is especially designed for computers with low hardware specifications like netbooks, mobile devices (e.g. MIDs) or older computers.</p>', 'screenshots': ['http://spins.fedoraproject.org/en/lxde/../static/images/screenshots/screenshot-lxde.jpg'], 'variants': {'x86_64': {'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/22/Live/x86_64/Fedora-Live-LXDE-x86_64-22-3.iso', 'sha256': '6a444fd233068e0ebebaed665453dd7238d1f7b8cc0930b7dd1c8a866ca0d90b', 'size': 828375040}, 'i686': {'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/22/Live/i386/Fedora-Live-LXDE-i686-22-3.iso', 'sha256': '2301cd9b664fc97602152da8550c6876e70859362c24fc183cd16cd398cac0d6', 'size': 882900992}}, 'summary': 'A light, fast, less-resource hungry desktop environment.'},
{'releaseDate': '', 'source': 'Spins', 'name': 'Fedora MATE-Compiz Desktop', 'logo': 'qrc:/mate_icon.png', 'description': u'<p>The MATE Compiz spin bundles MATE Desktop with Compiz Fusion. MATE Desktop is a lightweight, powerful Desktop designed with productivity and performance in mind. The default windows manager is Marco which is usable for all machines and VMs. Compiz Fusion is a beautiful 3D windowing manager with Emerald and GTK theming.</p><p>If you want a powerful, lightweight Fedora Desktop with 3D eyecandy you should definitely try the MATE Compiz spin.</p>', 'screenshots': ['http://spins.fedoraproject.org/en/mate-compiz/../static/images/screenshots/screenshot-matecompiz.jpg'], 'variants': {'x86_64': {'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/22/Live/x86_64/Fedora-Live-MATE_Compiz-x86_64-22-3.iso', 'sha256': '2bb1eb56d3cb0bd0f645fa3deac8489ea9cef1c6ca57115f87cfc5e2bd844175', 'size': 1288490188}, 'i686': {'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/22/Live/i386/Fedora-Live-MATE_Compiz-i686-22-3.iso', 'sha256': '3a1cb11c1d70d0a4c96f028ef59cf5dc3ae1379540556a8413430b85437ab527', 'size': 1288490188}}, 'summary': 'A classic Fedora Desktop. With wobbly Windows.'},
{'releaseDate': '', 'source': 'Spins', 'name': 'Fedora SoaS Desktop', 'logo': 'qrc:/soas_icon.png', 'description': u'<p>Sugar on a Stick is a Fedora-based operating system featuring the award-winning Sugar Learning Platform and designed to fit on an ordinary USB thumbdrive ("stick").</p><p>Sugar sets aside the traditional \u201coffice-desktop\u201d metaphor, presenting a child-friendly graphical environment. Sugar automatically saves your progress to a "Journal" on your stick, so teachers and parents can easily pull up "all collaborative web browsing sessions done in the past week" or "papers written with Daniel and Sarah in the last 24 hours" with a simple query rather than memorizing complex file/folder structures. Applications in Sugar are known as Activities, some of which are described below.</p><p>It is now deployable for the cost of a stick rather than a laptop; students can take their Sugar on a Stick thumbdrive to any machine - at school, at home, at a library or community center - and boot their customized computing environment without touching the host machine\u2019s hard disk or existing system at all.</p>', 'screenshots': ['http://spins.fedoraproject.org/en/soas/../static/images/screenshots/screenshot-soas.jpg'], 'variants': {'x86_64': {'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/22/Live/x86_64/Fedora-Live-SoaS-x86_64-22-3.iso', 'sha256': 'fc637d47f1590d3cc4f4ad2c725508238c40bdeb9b00dc1ecf1ea5e0f9093d41', 'size': 773849088}, 'i686': {'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/22/Live/i386/Fedora-Live-SoaS-i686-22-3.iso', 'sha256': '2c9928cb0aa505e011938ede1105da201f3414e1d80787ac079067d0c503cd8f', 'size': 663748608}}, 'summary': 'Discover. Reflect. Share. Learn.'},
{'releaseDate': '', 'source': '', 'name': 'Fedora Labs', 'logo': '', 'description': '', 'screenshots': '', 'variants': {'x86_64': {}, 'i686': {}, 'armv7hl': {}}, 'summary': 'Functional bundles for Fedora'},
{'releaseDate': '', 'source': 'Labs', 'name': 'Fedora Design Suite', 'logo': 'qrc:/design-suite_icon_grey.png', 'description': u'<p>Looking for a ready-to-go desktop environment brimming with free and open source multimedia production and publishing tools? Try the Design Suite, a Fedora Spin created by designers, for designers.</p><p>The Design Suite includes the favorite tools of the Fedora Design Team. These are the same programs we use to create all the artwork that you see within the Fedora Project, from desktop backgrounds to CD sleeves, web page designs, application interfaces, flyers, posters and more. From document publication to vector and bitmap editing or 3D modeling to photo management, the Design Suite has an application for you \u2014 and you can install thousands more from the Fedora universe of packages.</p>', 'screenshots': [], 'variants': {'x86_64': {'url': 'https://download.fedoraproject.org/pub/alt/releases/22/Spins/x86_64/Fedora-Live-Design_suite-x86_64-22-3.iso', 'sha256': 'c59e48d7ff05424465e20790083049f774e49f0906554bdec36d419a3149f3ac', 'size': 1825361100}, 'i686': {'url': 'https://download.fedoraproject.org/pub/alt/releases/22/Spins/i386/Fedora-Live-Design_suite-i686-22-3.iso', 'sha256': '474d101a6fd30e6a8a91bb18a02996b93d96b71423eb1bd6d8e14334215c1f86', 'size': 1825361100}}, 'summary': 'Visual design, multimedia production, and publishing suite of free and open source creative tools.'},
{'releaseDate': '', 'source': 'Labs', 'name': 'Fedora Games', 'logo': 'qrc:/games_icon_grey.png', 'description': u"<p>The Fedora Games spin offers a perfect showcase of the best games available in Fedora. The included games span several genres, from first-person shooters to real-time and turn-based strategy games to puzzle games.</p><p>Not all the games available in Fedora are included on this spin, but trying out this spin will give you a fair impression of Fedora's ability to run great games.</p>", 'screenshots': [], 'variants': {'x86_64': {'url': 'https://download.fedoraproject.org/pub/alt/releases/22/Spins/x86_64/Fedora-Live-Games-x86_64-22-3.iso', 'sha256': 'b412cba2accfa7150621609ef34c79a46417fb47322d7db64a548c765ffa2354', 'size': 4294967296}, 'i686': {'url': 'https://download.fedoraproject.org/pub/alt/releases/22/Spins/i386/Fedora-Live-Games-i686-22-3.iso', 'sha256': 'e4d318e193148756fcf61868f8d51a0a21ea347ea33c0af5da16a384d80a6dd8', 'size': 4294967296}}, 'summary': 'A collection and perfect show-case of the best games available in Fedora.'},
{'releaseDate': '', 'source': 'Labs', 'name': 'Fedora Jam', 'logo': 'qrc:/jam_icon_grey.png', 'description': u'<p>Fedora Jam is for audio enthusiasts and musicians who want to create, edit and produce audio and music on Linux. It comes with Jack, ALSA and Pulseaudio by default including a suite of programs to tailor your studio.</p><p>Fedora Jam is a full-featured audio creation spin. It includes all the tools needed to help create the music you want, anything from classical to jazz to Heavy metal. Included in Fedora Jam is full support for JACK and JACK to PulseAudio bridging, the newest release of Ardour, and a full set of lv2 plugins.</p>', 'screenshots': [], 'variants': {'x86_64': {'url': 'https://download.fedoraproject.org/pub/alt/releases/22/Spins/x86_64/Fedora-Live-Jam_KDE-x86_64-22-3.iso', 'sha256': 'e7b376161a293a877d187a2cfab49c147810f8e56729d0a1530f02446499277b', 'size': 1825361100}, 'i686': {'url': 'https://download.fedoraproject.org/pub/alt/releases/22/Spins/i386/Fedora-Live-Jam_KDE-i686-22-3.iso', 'sha256': '0026c11cb89f07df96c12d2a414418160963a39872e1faadc0d9bbd5e4c90aa2', 'size': 1825361100}}, 'summary': 'For audio enthusiasts and musicians who want to create, edit and produce audio and music on Linux.'},
{'releaseDate': '', 'source': 'Labs', 'name': 'Fedora Robotics Suite', 'logo': 'qrc:/robotics-suite_icon_grey.png', 'description': u'<p>The Fedora Robotics spin provides a wide variety of free and open robotics software packages. These range from hardware accessory libraries for the Hokuyo laser scanners or Katana robotic arm to software frameworks like Fawkes or Player and simulation environments such as Stage and RoboCup Soccer Simulation Server 2D/3D. It also provides a ready to use development environment for robotics including useful libraries such as OpenCV computer vision library, Festival text to speech system and MRPT.</p><p>The Robotics spin is targeted at people just discovering their interest in robotics as well as experienced roboticists. For the former we provide a readily usable simulation environment with an introductory hands-on demonstration, and for the latter we provide a full development environment, to be used immediately.</p>', 'screenshots': [], 'variants': {'x86_64': {'url': 'https://download.fedoraproject.org/pub/alt/releases/22/Spins/x86_64/Fedora-Live-Robotics-x86_64-22-3.iso', 'sha256': '06e4d9144b4a5bc57b3fc97827eb18537faea2e6df887b444a5cbfa519a1ab27', 'size': 2684354560}, 'i686': {'url': 'https://download.fedoraproject.org/pub/alt/releases/22/Spins/i386/Fedora-Live-Robotics-i686-22-3.iso', 'sha256': '5d6afbed4dfaf822c1cd86ba8605a6e8ebced5aaf563063147c43ad6380559b0', 'size': 2576980377}}, 'summary': 'A wide variety of free and open robotics software packages for beginners and experts in robotics.'},
{'releaseDate': '', 'source': 'Labs', 'name': 'Fedora Scientific', 'logo': 'qrc:/scientific_icon_grey.png', 'description': u'<p>Wary of reinstalling all the essential tools for your scientific and numerical work? The answer is here. Fedora Scientific Spin brings together the most useful open source scientific and numerical tools atop the goodness of the KDE desktop environment.</p><p>Fedora Scientific currently ships with numerous applications and libraries. These range from libraries such as the GNU Scientific library, the SciPy libraries, tools like Octave and xfig to typesetting tools like Kile and graphics programs such as Inkscape. The current set of packages include an IDE, tools and libraries for programming in C, C++, Python, Java and R. Also included along with are libraries for parallel computing such as the OpenMPI and OpenMP. Tools for typesetting, writing and publishing are included.</p>', 'screenshots': [], 'variants': {'x86_64': {'url': 'https://download.fedoraproject.org/pub/alt/releases/22/Spins/x86_64/Fedora-Live-Scientific_KDE-x86_64-22-3.iso', 'sha256': '060a54263da91160f50b30ea3a2bb96c92dca1c0766b9e7cc2dde6cfc3221335', 'size': 3221225472}, 'i686': {'url': 'https://download.fedoraproject.org/pub/alt/releases/22/Spins/i386/Fedora-Live-Scientific_KDE-i686-22-3.iso', 'sha256': '286e48dafc6a8ba0f22a482e6ff4f00e71f62ab919858e95b58ce6117a7bc322', 'size': 3221225472}}, 'summary': 'A bundle of open source scientific and numerical tools used in research.'},
{'releaseDate': '', 'source': 'Labs', 'name': 'Fedora Security Lab', 'logo': 'qrc:/security-lab_icon_grey.png', 'description': u'<p>The Fedora Security Lab provides a safe test environment to work on security auditing, forensics, system rescue and teaching security testing methodologies in universities and other organizations.</p><p>The spin is maintained by a community of security testers and developers. It comes with the clean and fast Xfce Desktop Environment and a customized menu that provides all the instruments needed to follow a proper test path for security testing or to rescue a broken system. The Live image has been crafted to make it possible to install software while running, and if you are running it from a USB stick created with LiveUSB Creator using the overlay feature, you can install and update software and save your test results permanently.</p>', 'screenshots': [], 'variants': {'x86_64': {'url': 'https://download.fedoraproject.org/pub/alt/releases/22/Spins/x86_64/Fedora-Live-Security-x86_64-22-3.iso', 'sha256': '52906c1767716098a059940d675a7ff7ba781b72e75924259effdbd426af72aa', 'size': 932184064}, 'i686': {'url': 'https://download.fedoraproject.org/pub/alt/releases/22/Spins/i386/Fedora-Live-Security-i686-22-3.iso', 'sha256': 'acb327698c63cc2fa533d6ad1be122701c728927c690cfc21043a22276d3aa68', 'size': 898629632}}, 'summary': 'A safe test environment to work on security auditing, forensics, system rescue and teaching security testing methodologies.'}]

releases = fedora_releases

if __name__ == '__main__':
    import pprint
    pprint.pprint(get_fedora_releases())
