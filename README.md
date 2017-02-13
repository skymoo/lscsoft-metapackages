Simple script which turns a yaml file like
```
---
####################
### lscsoft-all
####################
changelog:
  - date: 2016-12-14T19:04:10+01:00
    author: Carsten Aulbert <carsten.aulbert@ligo.org>
    changes:
      - |
        further tests
        another line
      - needed?
    version: 2016.12
  - date: 02/06/17 4:48pm EST
    author: Carsten Aulbert <carsten.aulbert@ligo.org>
    changes:
      - Test date string
    version: 1.0
desc_short: 'Metapackage to pull in all other lscsoft packages'
desc_long:
deps:
  gsl:
    deb: libgsl-dev (>> 1.4) | libgsl2-dev
    rpm: libgsl-devel (> 1.4), libgsl-devel(< 1.8)
  lscsoft-internal:
  lscsoft-external:
  lscsoft-ldas:
  lscsoft-auth:
maintainer: Carsten Aulbert <carsten.aulbert@ligo.org>
priority: optional
section: lscsoft
```

into `rpm` spec file like

```
Name: lscsoft-all
Version: 2016.12
Release: 1%{?dist}
Group: lscsoft
License: GPL
Summary: Metapackage to pull in all other lscsoft packages
Packager: Carsten Aulbert <carsten.aulbert@ligo.org>
BuildArch: noarch

Requires: libgsl-devel (> 1.4), libgsl-devel(< 1.8)
Requires: lscsoft-auth
Requires: lscsoft-external
Requires: lscsoft-internal 
Requires: lscsoft-ldas

%description
Metapackage to pull in all other lscsoft packages

%install

%files

%changelog
* Wed Dec 14 2016 Carsten Aulbert <carsten.aulbert@ligo.org> 2016.12
- further tests
  another line
- needed?
* Mon Jun 17 2002 Carsten Aulbert <carsten.aulbert@ligo.org> 1.0
- Test date string
```

and for Debian a set of files, e.g.
`README`:

```
Metapackage to pull in all other lscsoft packages
```

`copyright`:

```
Upstream Author(s): The LIGO Scientific Collaboration

Copyright: LIGO Scientific Collaboration

License: GPLv2 (or later)
```

`changelog.Debian`:

```
lscsoft-all (2016.12) unstable; urgency=medium

  * further tests
    another line

  * needed?

 -- Carsten Aulbert <carsten.aulbert@ligo.org>  Wed, 14 Dec 2016 19:04:10 +0100

lscsoft-all (1.0) unstable; urgency=medium

  * Test date string

 -- Carsten Aulbert <carsten.aulbert@ligo.org>  Mon, 17 Jun 2002 16:48:00 -0500

```

and finally, `control`
```
Section: lscsoft
Priority: optional
Standards-Version: 3.9.2

Package: lscsoft-all
Maintainer: Carsten Aulbert <carsten.aulbert@ligo.org>
Readme: README
Changelog: changelog.Debian
Copyright: copyright
Architecture: all
Depends: libgsl-dev (>> 1.4) | libgsl2-dev, lscsoft-auth, lscsoft-external, lscsoft-internal (>> 5.0), lscsoft-ldas
Description: Metapackage to pull in all other lscsoft packages
 Metapackage to pull in all other lscsoft packages
 ```