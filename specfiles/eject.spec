Summary: A program that ejects removable media using software control.
Name: eject
Version: 2.1.5
Release: 11%{dist}
License: GPL
Group: System Environment/Base
Source: http://metalab.unc.edu/pub/Linux/utils/disk-management/%{name}-%{version}.tar.gz
Source1: eject.pam
Patch1: eject-2.1.1-verbose.patch
Patch2: eject-timeout.patch
Patch3: eject-2.1.5-opendevice.patch
Patch4: eject-2.1.5-spaces.patch
Patch5: eject-2.1.5-lock.patch
Patch6: eject-2.1.5-umount.patch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
URL: http://www.pobox.com/~tranter
ExcludeArch: s390 s390x
BuildRequires: gettext
BuildRequires: automake
BuildRequires: autoconf
BuildRequires: libtool

%description
The eject program allows the user to eject removable media (typically
CD-ROMs, floppy disks or Iomega Jaz or Zip disks) using software
control. Eject can also control some multi-disk CD changers and even
some devices' auto-eject features.

Install eject if you'd like to eject removable media using software
control.

%prep
%setup -q -n %{name}
%patch1 -p1 -b .versbose
%patch2 -p1 -b .timeout
%patch3 -p0 -b .opendevice
%patch4 -p0 -b .spaces
%patch5 -p0 -b .lock
%patch6 -p1 -b .umount

%build
%configure
make

%install
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install

# pam stuff
install -m 755 -d %{buildroot}/%{_sysconfdir}/pam.d
install -m 644 %{SOURCE1} %{buildroot}/%{_sysconfdir}/pam.d/%{name}
install -m 755 -d %{buildroot}/%{_sysconfdir}/security/console.apps/
echo "FALLBACK=true" > %{buildroot}/%{_sysconfdir}/security/console.apps/%{name}

install -m 755 -d %{buildroot}/%{_sbindir}
pushd %{buildroot}/%{_bindir}
mv eject ../sbin
ln -s consolehelper eject
popd

%find_lang %{name}

%clean
rm -rf %{buildroot}

%files -f %{name}.lang
%defattr(-,root,root)
%doc README TODO COPYING ChangeLog
%attr(644,root,root) %{_sysconfdir}/security/console.apps/*
%attr(644,root,root) %{_sysconfdir}/pam.d/*
%{_bindir}/*
%{_sbindir}/*
%{_mandir}/man1/*

%changelog
* Wed Apr 02 2008 Zdenek Prikryl <zprikryl at, redhat.com> 2.1.5-11
- Added check if device is hotpluggable
- Resolves #438610

