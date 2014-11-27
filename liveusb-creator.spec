%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

%if (0%{?fedora} && 0%{?fedora} < 19) || (0%{?rhel} && 0%{?rhel} < 7)
%global with_desktop_vendor_tag 1
%else
%global with_desktop_vendor_tag 0
%endif

Name:           liveusb-creator
Version:        3.13.1
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
ExcludeArch:    %{arm}

BuildRequires:  python-devel, python-setuptools, PyQt4-devel, desktop-file-utils gettext

Requires:       syslinux
Requires:       PyQt4
Requires:       isomd5sum
Requires:       python-urlgrabber
Requires:       pyparted >= 2.0
Requires:       syslinux-extlinux
Requires:       udisks
Requires:       polkit
Requires:       polkit-gnome

%description
A liveusb creator from Live Fedora images

%prep
%setup -q

%build
%{__python} setup.py build
make mo

%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
%{__rm} -r liveusb/urlgrabber

# program needs root, move to sbin
mkdir -p %{buildroot}%{_sbindir}
mv %{buildroot}%{_bindir}/%{name} %{buildroot}%{_sbindir}/%{name}

# polkit stuff
mkdir -p %{buildroot}%{_datadir}/polkit-1/actions
%{__install} -p -m644 \
	org.fedoraproject.pkexec.run-liveusb-creator.policy \
	%{buildroot}%{_datadir}/polkit-1/actions/
%{__install} -p -m755 \
	liveusb-creator_polkit \
	%{buildroot}%{_bindir}/

desktop-file-install \
%if %{with_desktop_vendor_tag}
  --vendor fedora \
%endif
--dir=%{buildroot}%{_datadir}/applications           \
%{buildroot}/%{_datadir}/applications/liveusb-creator.desktop
%if %{with_desktop_vendor_tag}
rm -rf %{buildroot}/%{_datadir}/applications/liveusb-creator.desktop
%endif

%find_lang %{name}

%clean
rm -rf %{buildroot}

%files -f %{name}.lang
%defattr(-,root,root,-)
%doc README.rst LICENSE.txt
%{python_sitelib}/*
%{_bindir}/*
%{_sbindir}/*
%{_datadir}/applications/*liveusb-creator.desktop
%{_datadir}/pixmaps/fedorausb.png
%{_datadir}/appdata/%{name}.appdata.xml
#%{_datadir}/locale/*/LC_MESSAGES/liveusb-creator.mo
%{_datadir}/polkit-1/actions/org.fedoraproject.pkexec.run-liveusb-creator.policy

%changelog
* Thu Nov 27 2014 Luke Macken <lmacken@redhat.com> - 3.13.1-1
- Latest upstream release

* Thu Nov 27 2014 Gene Czarcinski <gczarcinski@gmail.com> 3.13.0-2
- convert to using polkit (pkexec) instead of consolehelper

* Wed Nov 26 2014 Luke Macken <lmacken@redhat.com> - 3.13.0-1
- Latest upstream release with bug fixes and interface improvements.

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.12.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Fri Feb 21 2014 Luke Macken <lmacken@redhat.com> 3.12.1-1
- Update to 3.12.1 with more translations

* Wed Oct 16 2013 Luke Macken <lmacken@redhat.com> 3.12.0-1
- Update to 3.12.0

* Wed Aug 14 2013 Luke Macken <lmacken@redhat.com> 3.11.8-6
- Fix the ExcludeArch for arm

* Sat Aug 10 2013 Luke Macken <lmacken@redhat.com> 3.11.8-5
- Exclude building for armhfp, since syslinux is not available.

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.11.8-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Wed Jun 26 2013 Adam Williamson <awilliam@redhat.com> - 3.11.8-3
- require usermode-gtk (or else it doesn't run from menus): #976415

* Fri Apr 26 2013 Jon Ciesla <limburgher@gmail.com> - 3.11.8-2
- Drop desktop vendor tag.

* Mon Apr 22 2013 Luke Macken <lmacken@redhat.com> - 3.11.8-1
- Update to 3.11.8

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.11.7-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Thu Jul 19 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.11.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Jun 12 2012 Luke Macken <lmacken@redhat.com> - 3.11.7-1
- Update to 3.11.7

* Mon Mar 19 2012 Luke Macken <lmacken@redhat.com> - 3.11.6-3
- Add an explicit udisks requirement (#796489)

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.11.6-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Nov 08 2011 Luke Macken <lmacken@redhat.com> - 3.11.6-1
- Update to 3.11.6

* Wed Nov 02 2011 Luke Macken <lmacken@redhat.com> - 3.11.5-1
- Update to 3.11.5

* Tue Jun 21 2011 Luke Macken <lmacken@redhat.com> - 3.11.4-1
- 3.11.4 bugfix release

* Tue Jun 21 2011 Luke Macken <lmacken@redhat.com> - 3.11.3-1
- 3.11.3 bugfix release

* Sun Jun 12 2011 Luke Macken <lmacken@redhat.com> - 3.11.2-1
- Fix traceback that occurs when extlinux is not installed (#712722)

* Tue May 24 2011 Luke Macken <lmacken@redhat.com> - 3.11.1-1
- Bump to support downloading Fedora 15

* Mon Apr 25 2011 Luke Macken <lmacken@redhat.com> - 3.11.0-1
- Latest upstream release

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.9.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Mon Jan 10 2011 Luke Macken <lmacken@redhat.com> - 3.9.3-1
- Update to 3.9.3
- Require syslinux-extlinux (#664093, #665002)

* Wed Jul 21 2010 David Malcolm <dmalcolm@redhat.com> - 3.9.2-2
- Rebuilt for https://fedoraproject.org/wiki/Features/Python_2.7/MassRebuild

* Tue Jun 15 2010 Luke Macken <lmacken@redhat.com> - 3.9.2-1
- 3.9.2

* Tue Dec 08 2009 Luke Macken <lmacken@redhat.com> - 3.9.1-1
- 3.9.1 bugfix release

* Tue Dec 01 2009 Luke Macken <lmacken@redhat.com> - 3.9-1
- 3.9 release

* Tue Dec 01 2009 Luke Macken <lmacken@redhat.com> - 3.8.9-1
- 3.8.9, fixes bug #540255

* Tue Dec 01 2009 Luke Macken <lmacken@redhat.com> - 3.8.8-1
- 3.8.8, bugfix release

* Tue Nov 17 2009 Luke Macken <lmacken@redhat.com> - 3.8.7-1
- 3.8.7, containing the F12 release

* Sat Nov 07 2009 Luke Macken <lmacken@redhat.com> - 3.8.6-1
- 3.8.6

* Thu Aug 27 2009 Luke Macken <lmacken@redhat.com> - 3.7.3-1
- 3.7.3

* Wed Aug 05 2009 Luke Macken <lmacken@redhat.com> - 3.7.2-1
- 3.7.2

* Sat Jun 27 2009 Luke Macken <lmacken@redhat.com> - 3.7.1-1
- 3.7.1

* Wed Jun 24 2009 Luke Macken <lmacken@redhat.com> - 3.7
- Latest upstream bugfix release

* Fri Jun 12 2009 Luke Macken <lmacken@redhat.com> - 3.6.8-1
- Latest upstream bugfix release

* Tue Jun 09 2009 Luke Macken <lmacken@redhat.com> - 3.6.7-1
- Fix a bug with ext formatted sticks

* Tue Jun 09 2009 Luke Macken <lmacken@redhat.com> - 3.6.6-1
- Update to v3.6.6
- Merge the dcon-unfreeze patch upstream
- Add Fedora 11 to the release list

* Wed May 20 2009 Christoph Wickert <cwickert@fedoraproject.org> - 3.6.5-3
- Make olpc.fth unfreeze disply for newer BIOSes than Q2E30 (#501688)

* Thu Apr 09 2009 Luke Macken <lmacken@redhat.com> 3.6.5-2
- Fix the checksum verification to support sha256

* Thu Apr 09 2009 Luke Macken <lmacken@redhat.com> 3.6.5-1
- Update to v3.6.5, which supports F11 beta, and the latest SoaS releases

* Wed Mar 18 2009 Luke Macken <lmacken@redhat.com> 3.6.4-1
- Update to v3.6.4, which works with the PyParted 2.0 API

* Thu Mar 12 2009 Luke Macken <lmacken@redhat.com> 3.6.3-1
- Update to v3.6.3

* Mon Mar 09 2009 Luke Macken <lmacken@redhat.com> 3.6-1
- Require pyparted
- Update to v3.6

* Fri Mar 06 2009 wwp <subscript@free.fr> 3.5-2
- Fix dd commands when output path contain whitespaces

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> 3.5-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Fri Jan 16 2009 Luke Macken <lmacken@redhat.com> 3.5-1
- Update to v3.5

* Fri Jan 16 2009 Luke Macken <lmacken@redhat.com> 3.4-1
- Update to 3.4.

* Fri Jan 16 2009 Luke Macken <lmacken@redhat.com> 3.3-2
- Require python-urlgrabber

* Thu Jan 15 2009 Luke Macken <lmacken@redhat.com> 3.3-1
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
