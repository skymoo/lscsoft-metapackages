#!/usr/bin/env python3

"""Generate all meta-package files bsed on the main config file
and what is already present under the target directory
"""

import shutil
import textwrap
from pathlib import Path

import jinja2
import yaml

# store path of this script
ROOT = Path(__file__).parent.absolute()
STAGE = ROOT / "stage"


# -- RPM ----------------------------------------

def _get_dependencies(pkg_data, build):
    # get dependencies
    dependencies = []
    if "deps" in pkg_data:
        for k, v in pkg_data["deps"].items():
            # add key as package name if value is nil
            # (simple package, same for all builds)
            if v is None:
                dependencies.append(k)
            # if our key exists use its value or the
            # package name itself if value is empty
            elif v.get(build, '') is None:
                dependencies.append(k)
            elif v.get(build):
                dependencies.extend(map(str.strip, v[build].split(',')))
    return dependencies


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
License: GPLv3+
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
# stage/pkgname/{deb,rpm}/ contain all necessary information to build meta-packages

def rpm_create_source(pkg_data):
    pkg = pkg_data["name"]

    # get dependencies
    dep_list = _get_dependencies(pkg_data, "rpm")

    # if extra headers are specified, add them verbatim here
    extra_headers = pkg_data.get("extra_headers", {}).get("rpm", [])

    # write spec file
    spec = STAGE / pkg / "rpm" / "{}.spec".format(pkg)
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

DEBIAN_COPYRIGHT = """
Upstream Author(s): The LIGO Scientific Collaboration

Copyright: LIGO Scientific Collaboration

License: GPLv2 (or later)
""".strip()

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

{% for line in pkg_data.get("extra_headers", {}).get("rpm", []) -%}
{{ line }}
{% endfor %}
{% for dep in dependencies -%}
Depends: {{ dep }}
{% endfor %}
Description: {{ pkg_data['desc_short'] }}
{{ pkg_data['desc_long'] }}
""".strip())


def deb_create_source(pkg_data):
    _deb_control(pkg_data)
    _deb_readme(pkg_data)
    _deb_changelog(pkg_data)
    _deb_copyright(pkg_data)


def _deb_readme(pkg_data):
    with (STAGE / pkg_data["name"] / "deb" / "README").open("w") as readme:
        print(pkg_data["desc_long"], file=readme)


def _deb_changelog(pkg_data):
    with (STAGE / pkg_data["name"] / "deb" / "changelog.Debian").open("w") as readme:
        print(
            DEBIAN_CHANGELOG_TEMPLATE.render(
                pkg_data=pkg_data,
            ).strip(),
            file=readme,
        )


def _deb_copyright(pkg_data):
    with (STAGE / pkg_data["name"] / "deb" / "copyright").open("w") as readme:
        print(
            DEBIAN_COPYRIGHT,
            file=readme,
        )


def _deb_control(pkg_data):
    pkg = pkg_data["name"]

    # get dependencies
    dep_list = _get_dependencies(pkg_data, "deb")

    # if extra headers are specified, add them verbatim here
    extra_headers = pkg_data.get("extra_headers", {}).get("deb", [])

    # reformat long description
    pkg_data["desc_long"] = _debian_format(
        pkg_data.get("desc_long", pkg_data["desc_short"]),
    )

    # write spec file
    control = STAGE / pkg / "deb" / "control"
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
  name: {{ pkg_data['name'] }}
  version: {{ pkg_data['changelog'][0]['version'] }}

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

about:
  home: https://git.ligo.org/packaging/lscsoft-metapackages
  license: GPLv3+
  license_family: GPL
  license_file: LICENSE
  summary: {{ pkg_data['desc_short'] }}
  description: |
    {{ pkg_data['desc_long'].strip()|indent }}
""")


def conda_create_recipe(pkg_data):
    # get dependencies
    dep_list = _get_dependencies(pkg_data, "conda")

    # determine noarch based on python lists
    haspython = any(dep.startswith("python") for dep in dep_list)
    if haspython and not any("# [py" in dep for dep in dep_list):
        noarch = "python"
    else:
        noarch = None

    # write spec file
    meta = STAGE / pkg / "conda" / "meta.yaml"
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


# -- main ---------------------------------------

BUILDERS = {
    "rpm": rpm_create_source,
    "deb": deb_create_source,
    "conda": conda_create_recipe,
}


if __name__ == "__main__":
    for meta_file in (ROOT / "meta").glob("*.yml"):
        print("Working on", meta_file)

        pkg = meta_file.stem
        with meta_file.open("r") as metaf:
            content = yaml.load(metaf, Loader=yaml.SafeLoader)

        # a few modifications need to be done (convenience)
        # parse date/times from changelog and sort them with newest first
        content["changelog"].sort(key=lambda x: x["date"], reverse=True)

        # add package name (inferred from YAML fname)
        content["name"] = pkg
        # add long description unless given
        content.setdefault("desc_long", content["desc_short"])

        # basic tests
        for key in {"changelog", "desc_short", "desc_long", "name", "maintainer", "priority", "section"}:
            assert content.get(key), "{} requires key '{}'".format(meta_file, key)

        # once we get here, check if we need to work at all on this one
        # for that, check its version file and compare to latest one from changelog
        versionfile = (STAGE / pkg / "version")
        try:
            with versionfile.open("r") as verf:
                version = verf.read().strip()
        except FileNotFoundError:
            pass
        else:
            if version == str(content['changelog'][0]['version']).strip():
                continue

        # build for each type
        for build, build_func in BUILDERS.items():
            if build not in content.get("skip", []):
                try:
                    (STAGE / pkg / build).mkdir(parents=True)
                except FileExistsError:
                    pass
                build_func(content)

        # all done, then update version file
        with versionfile.open("w") as verf:
            print(str(content["changelog"][0]["version"]), file=verf)
