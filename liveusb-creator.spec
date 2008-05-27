Name:           liveusb-creator
Version:        0.3.0
Release:        1%{?dist}
Summary:        TODO

Group:          
License:        
URL:            
Source0:        
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  PyQt4-devel
Requires:       PyQt4
Requires:       p7zip
Requires:       syslinux

%description


%prep
%setup -q


%build
%configure
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc



%changelog
