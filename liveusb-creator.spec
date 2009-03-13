%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           liveusb-creator
Version:        3.6.3
Release:        1%{?dist}
Summary:        A liveusb creator

Group:          Applications/System
License:        GPLv2
URL:            https://fedorahosted.org/liveusb-creator
Source0:        https://fedorahosted.org/releases/l/i/liveusb-creator/%{name}-%{version}.tar.bz2
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
ExcludeArch:    ppc
ExcludeArch:    ppc64

BuildRequires:  python-devel, python-setuptools, PyQt4-devel, desktop-file-utils gettext
Requires:       syslinux, PyQt4, usermode, isomd5sum
Requires:       python-urlgrabber
Requires:       pyparted

%description
A liveusb creator from Live Fedora images

%prep
%setup -q

%build
%{__python} setup.py build
make mo
make mo

%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
%{__rm} -r liveusb/urlgrabber

# Adjust for console-helper magic
mkdir -p %{buildroot}%{_sbindir}
mv %{buildroot}%{_bindir}/%{name} %{buildroot}%{_sbindir}/%{name}
ln -s ../bin/consolehelper %{buildroot}%{_bindir}/%{name}
mkdir -p %{buildroot}%{_sysconfdir}/pam.d
cp %{name}.pam %{buildroot}%{_sysconfdir}/pam.d/%{name}
mkdir -p %{buildroot}%{_sysconfdir}/security/console.apps
cp %{name}.console %{buildroot}%{_sysconfdir}/security/console.apps/%{name}

desktop-file-install --vendor="fedora"                    \
--dir=%{buildroot}%{_datadir}/applications           \
%{buildroot}/%{_datadir}/applications/liveusb-creator.desktop
rm -rf %{buildroot}/%{_datadir}/applications/liveusb-creator.desktop

%find_lang %{name}

%clean
rm -rf %{buildroot}

%files -f %{name}.lang
%defattr(-,root,root,-)
%doc README.txt LICENSE.txt
%{python_sitelib}/*
%{_bindir}/%{name}
%{_sbindir}/%{name}
%{_datadir}/applications/fedora-liveusb-creator.desktop
%{_datadir}/pixmaps/fedorausb.png
#%{_datadir}/locale/*/LC_MESSAGES/liveusb-creator.mo
%config(noreplace) %{_sysconfdir}/pam.d/%{name}
%config(noreplace) %{_sysconfdir}/security/console.apps/%{name}

%changelog
* Thu Mar 12 2009 Luke Macken <lmacken@redhat.com> 3.6.3-1
- Update to v3.6.3

* Mon Mar 07 2009 Luke Macken <lmacken@redhat.com> 3.6-1
- Require pyparted
- Update to v3.6

* Fri Mar 06 2009 wwp <subscript@free.fr> 3.5-2
- Fix dd commands when output path contain whitespaces

* Fri Jan 16 2009 Luke Macken <lmacken@redhat.com> 3.5-1
- Update to v3.5

* Fri Jan 16 2009 Luke Macken <lmacken@redhat.com> 3.4-1
- Update to 3.4.

* Fri Jan 16 2009 Luke Macken <lmacken@redhat.com> 3.3-2
- Require python-urlgrabber

* Fri Jan 15 2009 Luke Macken <lmacken@redhat.com> 3.3-1
- Update to 3.3

* Fri Jan 02 2009 Luke Macken <lmacken@redhat.com> 3.2-1
- Fixed some syslinux-related issues (#167)
- Fixed some windows-related logging problems (#337)
- Mitigate a DBus/HAL-related segfault by unmounting upon termination

* Thu Jan 01 2009 Luke Macken <lmacken@redhat.com> 3.1-1
- Latest upstream release, containing some windows-specific
  optimizations and fixes.

* Mon Dec 29 2008 Luke Macken <lmacken@redhat.com> 3.0-4
- Latest upstream release.
- Fedora 10 support
- Update to the latest sugar spin
- Lots of bug fixes and code improvements
- Improved OLPC support with the --xo flag
- Translation improvements
    - Greek translation (Nikos Charonitakis)
    - Slovak translation (Ondrej Sulek)
    - Catalan translation (Xavier Conde)
    - French translation (PabloMartin-Gomez)
    - Serbian (Milos Komarcevic)
    - Chinese (sainrysec)

* Fri Oct 03 2008 Luke Macken <lmacken@redhat.com> 3.0-2
- Exclude ppc and ppc64, as syslinux will not work on those architectures.

* Fri Aug 29 2008 Luke Macken <lmacken@redhat.com> 3.0-1
- Latest upstream release, containing various bugfixes
- Fedora 10 Beta support
- Brazilian Portuguese translation (Igor Pires Soares)
- Spanish translation (Domingo Becker)
- Malay translation (Sharuzzaman Ahmat Raslan)
- German Translation (Marcus Nitzschke, Fabian Affolter)
- Polish translation (Piotr Drąg)
- Portuguese translation (Valter Fukuoka)
- Czech translation (Adam Pribyl)

* Tue Aug 12 2008 Kushal Das <kushal@fedoraproject.org> 2.7-1
- Initial release
