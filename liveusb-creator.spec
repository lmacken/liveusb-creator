%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           liveusb-creator
Version:        2.7
Release:        1%{?dist}
Summary:        A liveusb creator

Group:          Applications/System
License:        GPLv2
URL:            https://fedorahosted.org/liveusb-creator
Source0:        https://fedorahosted.org/releases/l/i/liveusb-creator/%{name}-linux-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-devel, python-setuptools, PyQt4-devel, desktop-file-utils
Requires:       syslinux, PyQt4, usermode

%description
A liveusb creator from Live Fedora images

%prep
%setup -q


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# Adjust for console-helper magic
mkdir -p $RPM_BUILD_ROOT%{_sbindir}
mv $RPM_BUILD_ROOT%{_bindir}/%{name} $RPM_BUILD_ROOT%{_sbindir}/%{name}
ln -s ../bin/consolehelper $RPM_BUILD_ROOT%{_bindir}/%{name}
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/pam.d
cp %{name}.pam $RPM_BUILD_ROOT%{_sysconfdir}/pam.d/%{name}
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/security/console.apps
cp %{name}.console $RPM_BUILD_ROOT%{_sysconfdir}/security/console.apps/%{name}

desktop-file-install --vendor="fedora"                    \
--dir=${RPM_BUILD_ROOT}%{_datadir}/applications           \
%{buildroot}/%{_datadir}/applications/liveusb-creator.desktop
rm -rf %{buildroot}/%{_datadir}/applications/liveusb-creator.desktop

%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc README.txt LICENSE.txt
# For noarch packages: sitelib
%{python_sitelib}/*
%{_bindir}/*
%{_sbindir}/*
%{_datadir}/*
%config(noreplace) %{_sysconfdir}/pam.d/%{name}
%config(noreplace) %{_sysconfdir}/security/console.apps/%{name}

%changelog
* Tue Aug 12 2008 Kushal Das <kushal@fedoraproject.org> 2.7-1
- Initial release
