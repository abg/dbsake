%if 0%{?rhel} == 5
%global pyver 26
%global pybasever 2.6
%global __python /usr/bin/python%{pybasever}
%global __os_install_post %{__python26_os_install_post}
%endif

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:           dbsake
Version:        1.0.4
Release:        1%{?dist}
Summary:        Database administration toolkit for MySQL
Group:          Applications/Databases

License:        GPLv2
URL:            https://github.com/abg/dbsake
Source0:        https://github.com/abg/dbsake/archive/dbsake-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch
BuildRequires:  python%{?pyver}-devel
BuildRequires:  python%{?pyver}-setuptools

%description
DBSake is a collection of command-line tools to perform various DBA related
tasks for MySQL.


%prep
%setup -q -n %{name}-%{version}


%build
%{__python} setup.py build


%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
# install manpage
install --mode=0755 -d %{buildroot}%{_mandir}/man1
install --mode=0644 contrib/dbsake.1.man %{buildroot}%{_mandir}/man1/dbsake.1
 
%files
%doc
# For noarch packages: sitelib
%{python_sitelib}/*
%{_bindir}/dbsake
%{_mandir}/man1/dbsake.1*

%changelog
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
