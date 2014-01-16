%if 0%{?rhel} == 5
%global pyvertag 26
%global pyver 2.6
%endif

%{!?python_sitelib: %global python_sitelib %(%{__python}%{?pyver} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:           dbsake
Version:        1.0.3
Release:        1%{?dist}
Summary:        Database administration toolkit for MySQL
Group:          Applications/Databases

License:        GPLv2
URL:            https://github.com/abg/dbsake
Source0:        dbsake-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch
BuildRequires:  python%{?pyvertag}-devel
BuildRequires:  python%{?pyvertag}-setuptools
Requires:       python%{?pyvertag}-setuptools

%description
DBSake is a collection of command-line tools to perform various DBA related
tasks for MySQL.


%prep
%setup -q -n %{name}-%{version}


%build
%{__python}%{?pyver} setup.py build


%install
rm -rf %{buildroot}
%{__python}%{?pyver} setup.py install -O1 --skip-build --root %{buildroot}

 
%files
%doc
# For noarch packages: sitelib
%{python_sitelib}/*
%{_bindir}/dbsake


%changelog
