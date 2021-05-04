#!/usr/bin/env python3

"""Generate all meta-package files bsed on the main config file
and what is already present under the target directory
"""

import re
import shutil
import textwrap
from pathlib import Path

import jinja2
from dateutil import parser as dateparser
from ruamel import yaml

ROOT = Path.cwd().absolute()
STAGE = ROOT / "stage"

SELECTOR_REGEX = re.compile(
    r" # \[(.*)\](\Z|,)",
)

# supported distributions
RPM_DISTS = (
    "el7",
    "el8",
)
DEBIAN_DISTS = (
    "stretch",
    "buster",
    "bullseye",
    "bookworm",
    "trixie",
)


# improve datetime parsing
def timestamp_constructor(loader, node):
    return dateparser.parse(node.value)


yaml.add_constructor(
    'tag:yaml.org,2002:timestamp',
    timestamp_constructor,
    Loader=yaml.SafeLoader,
)


def _platform(dist):
    if dist in RPM_DISTS:
        return "rpm"
    if dist in DEBIAN_DISTS:
        return "deb"
    return dist


def _dist_and_platform(dist):
    plat = _platform(dist)
    if dist == plat:
        return (dist,)
    return (dist, plat)


def get_package_name(pkg_data, dist, default):
    #----------
    # Allow renaming of package via package_name attribute.
    # If not explicitly set for a distribution, then the
    #   default value (usually the filename) will be used.
    #
    # Ex:
    # package_name:
    #   deb: gds-dev
    #----------
    for key in _dist_and_platform(dist):
        try:
            return pkg_data["package_name"][key]
        except KeyError:
            pass
    return default


def _parse_key_comment(mapping, key):
    try:
        return mapping.ca.items[key][2].value.strip()
    except (AttributeError, KeyError):
        return None


def _parse_list_comment(parent, item):
    try:
        return parent.ca.items[item][0].value.strip()
    except (AttributeError, KeyError):
        return None


def _rejoin_comment(value, comment):
    return "{}  {}".format(value.strip(), comment or "").strip()


def _get_dependencies(pkg_data, dist):
    """Parse the dependencies for this distribution
    """
    for pkg, req in pkg_data.get("deps", {}).items():

        if req is None:  # no build specifics for any build
            yield pkg
            continue

        # find if package is specified by dist (e.g. 'buster')
        # or build (e.g. 'deb') if at all
        try:
            key = [
                key for key in _dist_and_platform(dist)
                if key is not None and key in req
            ][0]
        except IndexError:  # not specified
            continue

        # key is specified, if no value just use the parent name
        raw = req[key] or pkg

        # parse a comma-separated list
        if not isinstance(raw, list):
            raw = raw.split(",")
            comment = _parse_key_comment(req, key)
            if comment and len(raw) != 1:
                raise ValueError(
                    "invalid use of selector, one package per line please",
                )
            elif comment:
                yield _rejoin_comment(raw.pop(), _parse_key_comment(req, build))
            else:
                yield from raw
            continue

        # or a yaml list
        for i, dep in enumerate(raw):
            yield _rejoin_comment(dep, _parse_list_comment(raw, i))


def _get_extra_headers(pkg_data, dist):
    for key in _dist_and_platform(dist):
        return pkg_data.get("extra_headers", {}).get(key, [])
    return {}


def _debian_format(text, width=78):
    parts = text.split('\n\n')
    return '\n .\n'.join(
        "\n".join(textwrap.wrap(
            p,
            width=78,
            subsequent_indent=" ",
            initial_indent=" ",
        )) for p in parts
    )


# -- RPM ----------------------------------------

SPEC_TEMPLATE = jinja2.Template("""
Name: {{ pkg_data['name'] }}
Version: {{ pkg_data['changelog'][0]['version'] }}
Release: 1%{?dist}
License: GPL-3.0-or-later
URL: https://git.ligo.org/packaging/lscsoft-metapackages
Summary: {{ pkg_data['desc_short'] }}
BuildArch: noarch

{% for dep in dependencies -%}
Requires: {{ dep }}
{% endfor %}

{% for line in pkg_data.get("extra_headers", {}).get("rpm", []) -%}
{{ line }}
{% endfor %}

%description
{{ pkg_data["desc_long"] }}

%prep

%build

%install

%files

%changelog
{% for entry in pkg_data.get("changelog", []) -%}
* {{ entry["date"].strftime('%a %b %e %Y') }} {{ entry["author"] }} {{ entry["version"] }}-1
{% for change in entry["changes"] -%}
- {{ change.split('\n')|join('\n    ') }}
{% endfor %}
{% endfor %}
""".strip())

# standard directory layout (relative to $ROOT)
# meta/ contains the meta package definitions - one per file
# stage/pkgname/{conda,deb,rpm}/ contain all necessary information
# to build meta-packages

def rpm_create_source(pkg_data, dist):
    pkg = pkg_data["name"]

    # get dependencies
    dep_list = list(_get_dependencies(pkg_data, dist))

    # if extra headers are specified, add them verbatim here
    extra_headers = _get_extra_headers(pkg_data, dist)

    # write spec file
    spec = STAGE / pkg / dist / "{}.spec".format(pkg)
    with spec.open("w") as specf:
        print(
            SPEC_TEMPLATE.render(
                pkg_data=pkg_data,
                dependencies=dep_list,
                extra_headers=extra_headers,
            ).strip(),
            file=specf,
        )

# -- debian -------------------------------------

DEBIAN_CHANGELOG_TEMPLATE = jinja2.Template("""
{% for entry in pkg_data['changelog'] -%}
{{ pkg_data["name"] }} ({{ entry['version'] }}) unstable; urgency=medium
{% for change in entry['changes'] %}
  * {{ change.replace('\n', '\n  * ') }}
{%- endfor %}

 -- {{ entry['author'] }}  {{ entry['date'].strftime('%a, %d %b %Y %H:%M:%S %z') }}

{% endfor %}
""".strip())

DEBIAN_COPYRIGHT_TEMPLATE = jinja2.Template("""
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: {{ pkg_data["name"] }}
Upstream-Contact: The LIGO Scientific Collaboration
Source: https://git.ligo.org/packaging/lscsoft-metapackages

Files: *
Copyright: {{ pkg_data["date"].strftime("%Y") }} LIGO Scientific Collaboration
License: GPL-2.0-or-later

License: GPL-2.0-or-later
 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.
 .
 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
 .
 You should have received a copy of the GNU General Public License
 along with this program. If not, see <https://www.gnu.org/licenses/>.
 .
 On Debian systems, the complete text of the GNU General
 Public License can be found in `/usr/share/common-licenses/GPL-2'.

""".strip())

DEBIAN_CONTROL_TEMPLATE = jinja2.Template("""
Section: {{ pkg_data['section'] }}
Priority: {{ pkg_data['priority'] }}
Standards-Version: 3.9.8
Package: {{ pkg_data['name'] }}
Maintainer: {{ pkg_data['maintainer'] }}
Readme: README
Changelog: changelog.Debian
Copyright: copyright
Architecture: all

{% for line in pkg_data.get("extra_headers", {}).get("deb", []) -%}
{{ line }}
{% endfor %}
Depends:
{%- for dep in dependencies %}
 {{ dep }},
{%- endfor %}

Description: {{ pkg_data['desc_short'] }}
{{ pkg_data['desc_long'] }}
""".strip())


def deb_create_source(pkg_data, dist):
    _deb_control(pkg_data, dist)
    _deb_readme(pkg_data, dist)
    _deb_changelog(pkg_data, dist)
    _deb_copyright(pkg_data, dist)


def _deb_readme(pkg_data, dist):
    with (STAGE / pkg_data["name"] / dist / "README").open("w") as readme:
        print(pkg_data["desc_long"], file=readme)


def _deb_changelog(pkg_data, dist):
    with (STAGE / pkg_data["name"] / dist / "changelog.Debian").open("w") as readme:
        print(
            DEBIAN_CHANGELOG_TEMPLATE.render(
                pkg_data=pkg_data,
            ).strip(),
            file=readme,
        )


def _deb_copyright(pkg_data, dist):
    with (STAGE / pkg_data["name"] / dist / "copyright").open("w") as readme:
        print(
            DEBIAN_COPYRIGHT_TEMPLATE.render(
                pkg_data=pkg_data,
            ).strip(),
            file=readme,
        )


def _deb_control(pkg_data, dist):
    pkg = pkg_data["name"]

    # get dependencies
    dep_list = list(_get_dependencies(pkg_data, dist))

    # if extra headers are specified, add them verbatim here
    extra_headers = _get_extra_headers(pkg_data, dist)

    # reformat long description
    pkg_data["desc_long"] = _debian_format(
        pkg_data.get("desc_long", pkg_data["desc_short"]),
    )

    # write spec file
    control = STAGE / pkg / dist / "control"
    with control.open("w") as contf:
        print(
            DEBIAN_CONTROL_TEMPLATE.render(
                pkg_data=pkg_data,
                dependencies=dep_list,
                extra_headers=extra_headers,
            ).strip(),
            file=contf,
        )


# -- conda --------------------------------------

CONDA_TEMPLATE = jinja2.Template("""
package:
  name: "{{ pkg_data['name'] }}"
  version: "{{ pkg_data['changelog'][0]['version'] }}"

build:
  number: 0
{% if noarch %}  noarch: {{ noarch }}{%- endif %}

requirements:
{%- if not noarch and 'python' in dependencies %}
  host:
    - python
{%- endif %}
  run:
{%- for dep in dependencies|sort %}
    - {{ dep }}
{%- endfor %}

test:
  commands:
{%- for cmd in pkg_data.get("test", []) %}
    - {{ cmd }}
{%- endfor %}

about:
  home: "https://git.ligo.org/packaging/lscsoft-metapackages"
  license: "GPL-3.0-or-later"
  license_family: "GPL"
  license_file: "LICENSE"
  summary: "{{ pkg_data['desc_short'] }}"
  description: |
    {{ pkg_data['desc_long'].strip()|indent }}
""")


def conda_create_recipe(pkg_data, dist):
    # get dependencies
    dep_list = list(_get_dependencies(pkg_data, dist))

    # if any packages use selectors, they can't be noarch
    if any(map(SELECTOR_REGEX.search, dep_list)):
        noarch = None
    # otherwise they will be noarch generic since they don't
    # bundle any content
    else:
        noarch = "generic"

    # write spec file
    meta = STAGE / pkg / dist / "meta.yaml"
    with meta.open("w") as specf:
        print(
            CONDA_TEMPLATE.render(
                pkg_data=pkg_data,
                dependencies=dep_list,
                noarch=noarch,
            ).strip(),
            file=specf,
        )

    # copy license file into conda directory
    shutil.copyfile(
        str(ROOT / "LICENSE"),
        str(meta.parent / "LICENSE"),
    )


# -- tests --------------------------------------

TESTS_TEMPLATE = jinja2.Template("""
#!/bin/bash

set -ex

{%- for cmd in commands %}
{{ cmd }}
{%- endfor %}
""".strip())


def write_tests(pkg_data, dist):
    pkg = pkg_data["name"]
    with (STAGE / pkg / dist / "test.sh").open("w") as testf:
        print(
            TESTS_TEMPLATE.render(
                commands=content.get("test", []),
            ).strip(),
            file=testf,
        )


# -- main ---------------------------------------

BUILDERS = {
    "conda": conda_create_recipe,
}
BUILDERS.update({dist: rpm_create_source for dist in RPM_DISTS})
BUILDERS.update({dist: deb_create_source for dist in DEBIAN_DISTS})

if __name__ == "__main__":
    for meta_file in (ROOT / "meta").glob("*.yml"):
        print("Working on", meta_file)

        pkg = meta_file.stem
        with meta_file.open("r") as metaf:
            content = yaml.round_trip_load(metaf)

        # a few modifications need to be done (convenience)
        # parse date/times from changelog and sort them with newest first
        content["changelog"].sort(key=lambda x: x["date"], reverse=True)

        # add package name (inferred from YAML fname)
        content["name"] = pkg
        # add long description unless given
        content.setdefault("desc_long", content["desc_short"])
        # add date of most recent version
        content["date"] = content["changelog"][0]["date"]

        # basic tests
        for key in {"changelog", "desc_short", "desc_long", "name", "maintainer", "priority", "section"}:
            assert content.get(key), "{} requires key '{}'".format(meta_file, key)

        # build for each type
        for dist, build_func in BUILDERS.items():
            if any(
                x in content.get("skip", [])
                for x in _dist_and_platform(dist)
            ):
                continue
            content["name"] = get_package_name(content, dist, pkg)
            # once we get here, check if we need to work at all on this one
            # for that, check its version file and compare to latest one from changelog
            versionfile = (STAGE / content["name"] / "version")
            try:
                with versionfile.open("r") as verf:
                    version = verf.read().strip()
            except FileNotFoundError:
                pass
            else:
                if version == str(content['changelog'][0]['version']).strip():
                    continue

            try:
                (STAGE / content["name"] / dist).mkdir(parents=True)
            except FileExistsError:
                pass
            build_func(content, dist)
            write_tests(content, dist)

        # all done, then update version file
        with versionfile.open("w") as verf:
            print(str(content["changelog"][0]["version"]), file=verf)
