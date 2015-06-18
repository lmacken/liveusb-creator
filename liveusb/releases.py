# -*- coding: utf-8 -*-

import re
import traceback

from urlgrabber import urlread
from urlgrabber.grabber import URLGrabError

from pyquery import pyquery

from liveusb import _
from PyQt5.QtCore import QDateTime

BASE_URL = 'http://dl.fedoraproject.org'
PUB_URL = BASE_URL + '/pub/fedora/linux/releases/'
ALT_URL = BASE_URL + '/pub/alt/releases/'
ARCHES = ('armhfp', 'x86_64', 'i686', 'i386')


def getSpinDownload(url):
    d = pyquery.PyQuery(urlread(url))
    return d('div>div>div>p.gr>a.btn').attr('href')

def getSpinDetails(url, source):
    d = pyquery.PyQuery(urlread(url))
    spin = {
        'name': '',
        'description': '',
        'screenshots': [],
        'logo': 'qrc:/logo-fedora.svg',
        'url': '',
        'summary': '',
        'sha256': '',
        'size': 0,
        'releaseDate': '',
        'source': '',
        'arch': 'x86_64'
    }
    spin['source'] = source

    spin['name'] = d('title').html().strip()
    screenshot = d('img').filter('.img-responsive').attr('src')
    if screenshot:
        spin['screenshots'].append(url + "/.." + screenshot)

    for i in d('div').filter('.col-sm-8').html().split('\n'):
        #line = i.strip().replace('<p>', '').replace('</p>', '')
        line = i.strip()
        if len(line):
            spin['description'] += line

    spin['url'] = getSpinDownload(url + "/.." + d('a.btn').attr('href'))

    return spin

def getSpins(url, source):
    d = pyquery.PyQuery(urlread(url))
    spins = []

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
        'description': '',
        'screenshots': [],
        'logo': 'qrc:/logo-fedora.svg',
        'url': '',
        'summary': '',
        'sha256': '',
        'size': 0,
        'releaseDate': '',
        'source': '',
        'arch': 'x86_64'
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
        product['logo'] = 'qrc:/logo-color-workstation.png'
    if name == "Cloud":
        product['logo'] = 'qrc:/logo-color-cloud.png'
    if name == "Server":
        product['logo'] = 'qrc:/logo-color-server.png'

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

        products.append(getProductDetails(productUrl, productName))

    return products

def get_fedora_flavors():
    releases = [{'name': _('Custom OS...'),
              'description': _('Here you can choose a OS image from your hard drive to be written to your flash disk'),
              'logo': 'qrc:/icon-folder.svg',
              'screenshots': [],
              'url': '',
              'summary': _('<pick from file chooser>'),
              'sha256': '',
              'size': 0,
              'releaseDate': '',
              'source': 'Local',
              'arch': ''}]
    releases += getProducts('https://getfedora.org/')
    releases += getSpins("http://spins.fedoraproject.org", "Spins")
    releases += getSpins("http://labs.fedoraproject.org", "Labs")
    print releases

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
                                try:
                                    sha256, filename = line.split()
                                    if filename[0] != '*':
                                        continue
                                    filename = filename[1:]
                                    name = filename.replace('.iso', '')
                                    size = 0
                                    variant = ''
                                    version = ''
                                    try:
                                        for file in files.split('\n'):
                                            if file.find(filename) >= 0:
                                                match = re.search(r'.*?</a> +.*?  +([0-9.]+)([KMG]?)', file)
                                                size = float(match.group(1))
                                                if match.group(2) == 'G':
                                                    size *= 1024 * 1024 * 1024
                                                if match.group(2) == 'M':
                                                    size *= 1024 * 1024
                                                if match.group(2) == 'K':
                                                    size *= 1024
                                                size = int(size)
                                    except AttributeError:
                                        pass
                                    skip = False
                                    live = False
                                    netinst = False
                                    for i, part in enumerate(name.split('-')):
                                        if i == 1:
                                            if part == 'Live':
                                                skip = True
                                                live = True
                                            else:
                                                variant = part
                                        if i == 2:
                                            if part == 'netinst':
                                                skip = True
                                                netinst = True
                                            elif part == 'DVD':
                                                skip = True
                                            elif skip:
                                                variant = part
                                            else:
                                                arch = part
                                        if i == 3:
                                            if skip:
                                                arch = part
                                            else:
                                                version = part
                                        if i == 4 and skip:
                                            version = part
                                    fedora_releases.append(dict(
                                        fullName=name,
                                        size=size,
                                        variant=variant,
                                        arch=arch,
                                        version=version,
                                        live=live,
                                        netinst=netinst,
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
fedora_releases = [{'description': u'Here you can choose a OS image from your hard drive to be written to your flash disk', 'releaseDate': '', 'logo': 'qrc:/icon-folder.svg', 'screenshots': [], 'size': 0, 'name': u'Custom OS...', 'url': '', 'arch': '', 'summary': u'<pick from file chooser>', 'source': 'Local', 'sha256': ''}, {'description': "<p>Fedora Workstation is a reliable, user-friendly, and powerful operating system for your laptop or desktop computer. It supports a wide range of developers, from hobbyists and students to professionals in corporate environments.</p>\n        <blockquote><p>&#8220;The plethora of tools provided by  Fedora allows me to get the job done.  It just works.&#8221;</p>\n              <p align=right> \xe2\x80\x95 <em>Christine Flood, JVM performance engineer</em></p></blockquote><h3>Sleek user interface</h3>\n\t      <p>Focus on your code in the GNOME 3 desktop environment. GNOME is built with developer feedback and minimizes distractions, so you can concentrate on what's important.</p>\n        <h3>Complete open source toolbox</h3>\n\t      <p>Skip the drag of trying to find or build the tools you need. With Fedora's complete set of open source languages, tools, and utilities, everything is a click or command line away. There's even project hosting and repositories like COPR to make your code and builds available quickly to the community.</p>\n        <h3>GNOME Boxes &amp; other virt tools</h3>\n\t      <p>Get virtual machines up and running quickly to test your code on multiple platforms using GNOME Boxes. Or dig into powerful, scriptable virtualization tools for even more control.</p>\n        <h3>Built-in Docker support</h3>\n\t      <p>Containerize your own apps, or deploy containerized apps out of the box on Fedora, using the latest technology like Docker.</p>\n        ", 'releaseDate': '', 'logo': 'qrc:/logo-color-workstation.png', 'screenshots': [], 'size': 0, 'name': 'Workstation', 'url': '', 'arch': 'x86_64', 'summary': "This is the Linux workstation you've been waiting for.", 'source': 'Workstation', 'sha256': ''}, {'description': "<blockquote><p>&#8220;The simplicity introduced with rolekit and cockpit have made server deployments a breeze. What took me a few days on other operating systems took less than an hour with Fedora 22 Server. It just works.&#8221;</p>\n            <p align=right> \xe2\x80\x95 <em>Dan Mossor, Systems Engineer</em></p></blockquote><p>Fedora Server is a powerful, flexible operating system that includes the best and latest datacenter technologies. It puts you in control of all your infrastructure and services.</p>\n        <h3>Cockpit</h3>\n\t      <p>Manage your system easily with Cockpit's powerful, modern interface. View and monitor system performance and status, and deploy and manage container-based services.</p>\n        <h3>Server Roles and Rolekit</h3>\n\t        <p>There's no need to set up your server from scratch when you use server roles. Server roles plug into your Fedora Server system, providing a well-integrated service on top of the Fedora Server platform. Deploy and manage these prepared roles simply using the Rolekit tool.</p>\n        <h3>OpenLMI tools</h3>\n\t        <p>Manage a wide variety of system parameters with OpenLMI. Simplify administration using its unified command set and powerful Python scripting interface.</p>\n        <h3>FreeIPA identity management</h3>\n\t      <p>Level up your Linux network with advanced identity management. Manage users, systems, and policy throughout your environment with FreeIPA, the engine that drives Fedora Server's Domain Controller role.</p>\n        <blockquote><p>&#8220;The Docker Role for Fedora Server was simple and fast to install so that you can run your Docker images. This makes a great testbed for beginners and experts with docker so that they can develop their applications on the fly.&#8221;</p>\n            <p align=right> \xe2\x80\x95 <em>John Unland, Information Systems Student</em></p></blockquote>", 'releaseDate': '', 'logo': 'qrc:/logo-color-server.png', 'screenshots': [], 'size': 0, 'name': 'Server', 'url': '', 'arch': 'x86_64', 'summary': 'The latest technology. A stable foundation. Together, for your applications and services.', 'source': 'Server', 'sha256': ''}, {'description': "<blockquote><p>&#8220;Fedora 22 gives me the balance I'm looking for &#8212; a leading edge operating system with enterprise-level tools for fast provisioning and configuration.&#8221;</p>\n            <p align=right> \xe2\x80\x95 <em>Major Hayden, Principal Architect at Rackspace</em></p></blockquote><h2>Minimal, fast, flexible</h2>\n\t      <p>Everything you need, and nothing you don't. The Fedora Cloud Base image is smaller, so you can deploy faster. Then use the universe of services and tools in Fedora to customize, so your cloud is right for you.</p>\n        <h2>Public or private</h2>\n\t      <p>Deploy and run Fedora Cloud in public or private cloud infrastructure, using the industry standard tools cloud-init and OpenStack Heat. Wherever you run your cloud, Fedora is ready to go.</p>\n        <h2>Designed for containers</h2>\n\t      <p>Want easy, scalable app deployment? Fedora Atomic Host is optimized and streamlined to run Docker containers out of the box. Whether you're rolling out a handful of containers, or scaling up to meet incredible demand, you can do it with Fedora Atomic Host.</p>\n        <h2>Project Atomic inside</h2>\n\t      <p>The new Project Atomic update system works like git for your operating system. Now you can update and roll back with confidence and minimal downtime.</p>\n        ", 'releaseDate': '', 'logo': 'qrc:/logo-color-cloud.png', 'screenshots': [], 'size': 0, 'name': 'Cloud', 'url': '', 'arch': 'x86_64', 'summary': 'Lean. Powerful. Everycloud ready.', 'source': 'Cloud', 'sha256': ''}, {'description': u'<p>The Fedora KDE Plasma Desktop Edition is a powerful Fedora-based operating system utilizing the KDE Plasma Desktop as the main user interface.</p><p>Fedora KDE Plasma Desktop comes with many pre-selected top quality applications that suit all modern desktop use cases - from online communication like web browsing, instant messaging and electronic mail correspondence, through multimedia and entertainment, to an advanced productivity suite, including office applications and enterprise grade personal information management.</p><p>All KDE applications are well integrated, with a similar look and feel and an easy to use interface, accompanied by an outstanding graphical appearance.</p>', 'releaseDate': '', 'logo': 'qrc:/logo-fedora.svg', 'screenshots': ['http://spins.fedoraproject.org/en/kde/../static/images/screenshots/screenshot-kde.jpg'], 'size': 0, 'name': 'Fedora KDE Plasma Desktop', 'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/22/Live/x86_64/Fedora-Live-KDE-x86_64-22-3.iso', 'arch': 'x86_64', 'summary': 'A complete, modern desktop built using the KDE Plasma Desktop.', 'source': 'Spins', 'sha256': ''}, {'description': u'<p>The Fedora Xfce spin showcases the Xfce desktop, which aims to be fast and lightweight, while still being visually appealing and user friendly.</p><p>Fedora Xfce is a full-fledged desktop using the freedesktop.org standard.</p>', 'releaseDate': '', 'logo': 'qrc:/logo-fedora.svg', 'screenshots': ['http://spins.fedoraproject.org/en/xfce/../static/images/screenshots/screenshot-xfce.jpg'], 'size': 0, 'name': 'Fedora Xfce Desktop', 'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/22/Live/x86_64/Fedora-Live-Xfce-x86_64-22-3.iso', 'arch': 'x86_64', 'summary': 'A complete, well-integrated Xfce Desktop.', 'source': 'Spins', 'sha256': ''}, {'description': u'<p>LXDE, the "Lightweight X11 Desktop Environment", is an extremely fast, performant, and energy-saving desktop environment. It maintained by an international community of developers and comes with a beautiful interface, multi-language support, standard keyboard shortcuts and additional features like tabbed file browsing.</p><p>LXDE is not designed to be powerful and bloated, but to be usable and slim. A main goal of LXDE is to keep computer resource usage low. It is especially designed for computers with low hardware specifications like netbooks, mobile devices (e.g. MIDs) or older computers.</p>', 'releaseDate': '', 'logo': 'qrc:/logo-fedora.svg', 'screenshots': ['http://spins.fedoraproject.org/en/lxde/../static/images/screenshots/screenshot-lxde.jpg'], 'size': 0, 'name': 'Fedora LXDE Desktop', 'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/22/Live/x86_64/Fedora-Live-LXDE-x86_64-22-3.iso', 'arch': 'x86_64', 'summary': 'A light, fast, less-resource hungry desktop environment.', 'source': 'Spins', 'sha256': ''}, {'description': u'<p>The MATE Compiz spin bundles MATE Desktop with Compiz Fusion. MATE Desktop is a lightweight, powerful Desktop designed with productivity and performance in mind. The default windows manager is Marco which is usable for all machines and VMs. Compiz Fusion is a beautiful 3D windowing manager with Emerald and GTK theming.</p><p>If you want a powerful, lightweight Fedora Desktop with 3D eyecandy you should definitely try the MATE Compiz spin.</p>', 'releaseDate': '', 'logo': 'qrc:/logo-fedora.svg', 'screenshots': ['http://spins.fedoraproject.org/en/mate-compiz/../static/images/screenshots/screenshot-matecompiz.jpg'], 'size': 0, 'name': 'Fedora MATE-Compiz Desktop', 'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/22/Live/x86_64/Fedora-Live-MATE_Compiz-x86_64-22-3.iso', 'arch': 'x86_64', 'summary': 'A classic Fedora Desktop. With wobbly Windows.', 'source': 'Spins', 'sha256': ''}, {'description': u'<p>Sugar on a Stick is a Fedora-based operating system featuring the award-winning Sugar Learning Platform and designed to fit on an ordinary USB thumbdrive ("stick").</p><p>Sugar sets aside the traditional \u201coffice-desktop\u201d metaphor, presenting a child-friendly graphical environment. Sugar automatically saves your progress to a "Journal" on your stick, so teachers and parents can easily pull up "all collaborative web browsing sessions done in the past week" or "papers written with Daniel and Sarah in the last 24 hours" with a simple query rather than memorizing complex file/folder structures. Applications in Sugar are known as Activities, some of which are described below.</p><p>It is now deployable for the cost of a stick rather than a laptop; students can take their Sugar on a Stick thumbdrive to any machine - at school, at home, at a library or community center - and boot their customized computing environment without touching the host machine\u2019s hard disk or existing system at all.</p>', 'releaseDate': '', 'logo': 'qrc:/logo-fedora.svg', 'screenshots': ['http://spins.fedoraproject.org/en/soas/../static/images/screenshots/screenshot-soas.jpg'], 'size': 0, 'name': 'Fedora SoaS Desktop', 'url': 'https://download.fedoraproject.org/pub/fedora/linux/releases/22/Live/x86_64/Fedora-Live-SoaS-x86_64-22-3.iso', 'arch': 'x86_64', 'summary': 'Discover. Reflect. Share. Learn.', 'source': 'Spins', 'sha256': ''}, {'description': u'<p>Looking for a ready-to-go desktop environment brimming with free and open source multimedia production and publishing tools? Try the Design Suite, a Fedora Spin created by designers, for designers.</p><p>The Design Suite includes the favorite tools of the Fedora Design Team. These are the same programs we use to create all the artwork that you see within the Fedora Project, from desktop backgrounds to CD sleeves, web page designs, application interfaces, flyers, posters and more. From document publication to vector and bitmap editing or 3D modeling to photo management, the Design Suite has an application for you \u2014 and you can install thousands more from the Fedora universe of packages.</p>', 'releaseDate': '', 'logo': 'qrc:/logo-fedora.svg', 'screenshots': [], 'size': 0, 'name': 'Design Suite', 'url': 'https://download.fedoraproject.org/pub/alt/releases/22/Spins/x86_64/Fedora-Live-Design_suite-x86_64-22-3.iso', 'arch': 'x86_64', 'summary': 'Visual design, multimedia production, and publishing suite of free and open source creative tools.', 'source': 'Labs', 'sha256': ''}, {'description': u"<p>The Fedora Games spin offers a perfect showcase of the best games available in Fedora. The included games span several genres, from first-person shooters to real-time and turn-based strategy games to puzzle games.</p><p>Not all the games available in Fedora are included on this spin, but trying out this spin will give you a fair impression of Fedora's ability to run great games.</p>", 'releaseDate': '', 'logo': 'qrc:/logo-fedora.svg', 'screenshots': [], 'size': 0, 'name': 'Games', 'url': 'https://download.fedoraproject.org/pub/alt/releases/22/Spins/x86_64/Fedora-Live-Games-x86_64-22-3.iso', 'arch': 'x86_64', 'summary': 'A collection and perfect show-case of the best games available in Fedora.', 'source': 'Labs', 'sha256': ''}, {'description': u'<p>Fedora Jam is for audio enthusiasts and musicians who want to create, edit and produce audio and music on Linux. It comes with Jack, ALSA and Pulseaudio by default including a suite of programs to tailor your studio.</p><p>Fedora Jam is a full-featured audio creation spin. It includes all the tools needed to help create the music you want, anything from classical to jazz to Heavy metal. Included in Fedora Jam is full support for JACK and JACK to PulseAudio bridging, the newest release of Ardour, and a full set of lv2 plugins.</p>', 'releaseDate': '', 'logo': 'qrc:/logo-fedora.svg', 'screenshots': [], 'size': 0, 'name': 'Jam', 'url': 'https://download.fedoraproject.org/pub/alt/releases/22/Spins/x86_64/Fedora-Live-Jam_KDE-x86_64-22-3.iso', 'arch': 'x86_64', 'summary': 'For audio enthusiasts and musicians who want to create, edit and produce audio and music on Linux.', 'source': 'Labs', 'sha256': ''}, {'description': u'<p>The Fedora Robotics spin provides a wide variety of free and open robotics software packages. These range from hardware accessory libraries for the Hokuyo laser scanners or Katana robotic arm to software frameworks like Fawkes or Player and simulation environments such as Stage and RoboCup Soccer Simulation Server 2D/3D. It also provides a ready to use development environment for robotics including useful libraries such as OpenCV computer vision library, Festival text to speech system and MRPT.</p><p>The Robotics spin is targeted at people just discovering their interest in robotics as well as experienced roboticists. For the former we provide a readily usable simulation environment with an introductory hands-on demonstration, and for the latter we provide a full development environment, to be used immediately.</p>', 'releaseDate': '', 'logo': 'qrc:/logo-fedora.svg', 'screenshots': [], 'size': 0, 'name': 'Robotics Suite', 'url': 'https://download.fedoraproject.org/pub/alt/releases/22/Spins/x86_64/Fedora-Live-Robotics-x86_64-22-3.iso', 'arch': 'x86_64', 'summary': 'A wide variety of free and open robotics software packages for beginners and experts in robotics.', 'source': 'Labs', 'sha256': ''}, {'description': u'<p>Wary of reinstalling all the essential tools for your scientific and numerical work? The answer is here. Fedora Scientific Spin brings together the most useful open source scientific and numerical tools atop the goodness of the KDE desktop environment.</p><p>Fedora Scientific currently ships with numerous applications and libraries. These range from libraries such as the GNU Scientific library, the SciPy libraries, tools like Octave and xfig to typesetting tools like Kile and graphics programs such as Inkscape. The current set of packages include an IDE, tools and libraries for programming in C, C++, Python, Java and R. Also included along with are libraries for parallel computing such as the OpenMPI and OpenMP. Tools for typesetting, writing and publishing are included.</p>', 'releaseDate': '', 'logo': 'qrc:/logo-fedora.svg', 'screenshots': [], 'size': 0, 'name': 'Scientific', 'url': 'https://download.fedoraproject.org/pub/alt/releases/22/Spins/x86_64/Fedora-Live-Scientific_KDE-x86_64-22-3.iso', 'arch': 'x86_64', 'summary': 'A bundle of open source scientific and numerical tools used in research.', 'source': 'Labs', 'sha256': ''}, {'description': u'<p>The Fedora Security Lab provides a safe test environment to work on security auditing, forensics, system rescue and teaching security testing methodologies in universities and other organizations.</p><p>The spin is maintained by a community of security testers and developers. It comes with the clean and fast Xfce Desktop Environment and a customized menu that provides all the instruments needed to follow a proper test path for security testing or to rescue a broken system. The Live image has been crafted to make it possible to install software while running, and if you are running it from a USB stick created with LiveUSB Creator using the overlay feature, you can install and update software and save your test results permanently.</p>', 'releaseDate': '', 'logo': 'qrc:/logo-fedora.svg', 'screenshots': [], 'size': 0, 'name': 'Security Lab', 'url': 'https://download.fedoraproject.org/pub/alt/releases/22/Spins/x86_64/Fedora-Live-Security-x86_64-22-3.iso', 'arch': 'x86_64', 'summary': 'A safe test environment to work on security auditing, forensics, system rescue and teaching security testing methodologies.', 'source': 'Labs', 'sha256': ''}]

releases = fedora_releases
