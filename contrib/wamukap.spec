#
# spec file for package python-wamukap
#
# Copyright (c) 2021 SUSE LLC
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/
#


%{?!python_module:%define python_module() python-%{**} python3-%{**}}
Name:           wamukap
Version:        0.0.2
Release:        0
Summary:        Website Availability Monitor using Kafka and PostgreSQL
License:        Apache-2.0
URL:            https://github.com/rhafer/wamukap
Source:         wamukap-%{version}.tar.gz
Source1:        system-user-wamukap.conf
BuildRequires:  python-rpm-macros
BuildRequires:  python3-aiohttp
BuildRequires:  python3-aiokafka
BuildRequires:  python3-aiopg
BuildRequires:  python3-setuptools
BuildRequires:  python3-toml
BuildRequires:  fdupes
BuildRequires:  sysuser-tools
Requires:       python3-aiopg
Requires:       python3-aiohttp
Requires:       python3-aiokafka
Requires:       python3-toml
%sysusers_requires
BuildArch:      noarch

%description
Website Availability Monitor using Kafka and PostgreSQL

%prep
%setup -q -n wamukap-%{version}

%build
%py3_build
%sysusers_generate_pre %{SOURCE1} %{name} system-user-wamukap.conf

%install
%py3_install
install -d %{buildroot}%{_sysconfdir}/%{name}
install -m 640 %{_builddir}/%{name}-%{version}/%{name}.toml %{buildroot}%{_sysconfdir}/%{name}
install -d %{buildroot}%{_unitdir}/
install  %{_builddir}/%{name}-%{version}/contrib/%{name}-producer.service %{buildroot}%{_unitdir}
install  %{_builddir}/%{name}-%{version}/contrib/%{name}-consumer.service %{buildroot}%{_unitdir}
mkdir -p %{buildroot}%{_sysusersdir}
install -m 0644 %{SOURCE1} %{buildroot}%{_sysusersdir}/

%pre -f %{name}.pre
%service_add_pre %{name}-producer.service %{name}-consumer.service

%post
%service_add_post %{name}-producer.service %{name}-consumer.service

%preun
%service_del_preun %{name}-producer.service %{name}-consumer.service

%postun
%service_del_postun %{name}-producer.service %{name}-consumer.service


%files
%{_sysusersdir}/system-user-%{name}.conf
%dir %{_sysconfdir}/%{name}
%config(noreplace) %attr(640,wamukap,wamukap) %{_sysconfdir}/%{name}/%{name}.toml
%doc README.rst
%license LICENSE
%{python_sitelib}/*
%{_bindir}/wamukap*
%{_unitdir}/*.service

%changelog
