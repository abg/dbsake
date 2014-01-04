%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:           dbsake
Version:        1.0.0
Release:        1%{?dist}
Summary:        Database administration toolkit for MySQL

License:        GPLv2
URL:            https://github.com/abg/dbsake
Source0:        dbsake-1.0.0.tar.gz

BuildArch:      noarch
BuildRequires:  python-devel
BuildRequires:  python-setuptools
Requires:       python-setuptools

%description
DBSake is a collection of command-line tools to perform various DBA related
tasks for MySQL.


%prep
%setup -q


%build
# Remove CFLAGS=... for noarch packages (unneeded)
CFLAGS="%{optflags}" %{__python} setup.py build


%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --skip-build --root %{buildroot}

 
%files
%doc
# For noarch packages: sitelib
%{python_sitelib}/*
%{_bindir}/dbsake


%changelog
