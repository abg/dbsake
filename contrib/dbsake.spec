%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:           dbsake
Version:        2.0.0
Release:        1%{?dist}
Summary:        A DBA's (s)wiss-(a)rmy-(k)nif(e) for mysql
Group:          Applications/Databases

License:        GPLv2
URL:            https://github.com/abg/dbsake
Source0:        https://github.com/abg/dbsake/archive/dbsake-%{version}%{?tag}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch
BuildRequires:  python-devel
BuildRequires:  python-setuptools
Requires:       python-click >= 2.0
Requires:       python-jinja2 >= 2.2.1

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
# remove pkg_resources dependency from setup.py console_scripts
cat <<EOF > %{buildroot}%{_bindir}/dbsake
#!%{__python}
import sys

import dbsake.cli

if __name__ == '__main__':
    sys.exit(dbsake.cli.main())
EOF
chmod 0755 %{buildroot}%{_bindir}/dbsake


%files
%doc README.rst HISTORY.rst LICENSE
# For noarch packages: sitelib
%{python_sitelib}/*
%{_bindir}/dbsake

%changelog
* Tue Aug 05 2014 Andrew Garner <andrew.garner@rackspace.com> - 2.0.0-1
- Sample rpm spec for 2.0.0
