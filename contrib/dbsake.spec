%if 0%{?rhel} == 5
%global pyver 26
%global pybasever 2.6
%global __python /usr/bin/python%{pybasever}
%global __os_install_post %{__python26_os_install_post}
%endif

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:           dbsake
Version:        1.0.9
Release:        1%{?dist}
Summary:        A DBA's (s)wiss-(a)rmy-(k)nif(e) for mysql
Group:          Applications/Databases

License:        GPLv2
URL:            https://github.com/abg/dbsake
Source0:        https://github.com/abg/dbsake/archive/dbsake-%{version}%{?tag}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch
BuildRequires:  python%{?pyver}-devel
BuildRequires:  python%{?pyver}-setuptools

%description
dbsake (pronounced "dee-bee sah-kay") is a set of commands to assist with:

- Parsing MySQL .frm files and output DDL
- Splitting mysqldump output into a file per object
- Patching a my.cnf to remove or convert deprecated options
- Deploying a new standalone MySQL "sandbox" instance
- Decoding/encoding MySQL filenames
- Managing OS caching for a set of files

Read the documentation at: http://docs.dbsake.net

%prep
%setup -q -n %{name}-%{version}%{?tag}


%build
%{__python} setup.py build


%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
# install manpage
install --mode=0755 -d %{buildroot}%{_mandir}/man1
install --mode=0644 contrib/dbsake.1.man %{buildroot}%{_mandir}/man1/dbsake.1
cat <<EOF > %{buildroot}%{_bindir}/dbsake
#!%{__python}
import sys
if __name__ == '__main__':
    sys.exit(__import__('dbsake').main())
EOF
chmod 0755 %{buildroot}%{_bindir}/dbsake


%files
%doc README.md CHANGES LICENSE
# For noarch packages: sitelib
%{python_sitelib}/*
%{_bindir}/dbsake
%{_mandir}/man1/dbsake.1*

%changelog
* Wed Jul 09 2014 "Adnrew Garner <andrew.garner@rackspace.com>" - 1.0.9-1
- New release

* Wed Apr 02 2014 "Andrew Garner <andrew.garner@rackspace.com>" - 1.0.8-1
- New release

* Thu Feb 20 2014 Andrew Garner <andrew.garner@rackspace.com> - 1.0.7-1
- New release

* Mon Feb 17 2014 Andrew Garner <andrew.garner@rackspace.com> - 1.0.6-1
- New release

* Fri Jan 31 2014 Andrew Garner <andrew.garner@rackspace.com> - 1.0.5-1
- New release

* Fri Jan 24 2014 Andrew Garner <andrew.garner@rackspace.com> - 1.0.4-1
- Added optional %%tag to allow building -dev releases
- Overwrite setuptools generated %%{_bindir}/dbsake to remove runtime
  dependency on setuptools

* Thu Jan 16 2014 Andrew Garner <andrew.garner@rackspace.com> - 1.0.3-1
- Added %%pyver and %%pyvertag to allow building against EPEL5
  where python2.6 is not the default python version
- New release

* Tue Jan 07 2014 Andrew Garner <andrew.garner@rackspace.com> - 1.0.2-1
- New release

* Mon Jan 06 2014 Andrew Garner <andrew.garner@rackspace.com> - 1.0.1-1
- New release

* Thu Jan 02 2014 Andrew Garner <andrew.garner@rackspace.com> - 1.0.0-1
- Initial spec from 1.0.0
