#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Generate a docs page for the LSCSoft Metpackages
"""

import argparse
import re
from operator import itemgetter
from pathlib import Path

import jinja2
import ruamel.yaml

import generate

yaml = ruamel.yaml.YAML()

PACKAGE_MANAGERS = {
    "conda": "Conda",
    "deb": "Debian",
    "rpm": "RHEL",
}

INDEX_TEMPLATE = jinja2.Template("""---
title: Introduction
---

# IGWN Software Metapackages

This page describes the metapackages that are available in the IGWN
Software Distributions to simplify software envirnoment configuration.

See the [_User guide_](guide.md) for instructions on how to configure and
use the metapackages, and also how to propose changes or additions.

The available metapackages are:

| Package name | Description |
| ------------ | ----------- |
{%- for pkg in metapackages %}
| [`{{ pkg['name'] }}`]({{ pkg['name'] }}.md) | {{ pkg['desc_short'] }} |{% endfor %}

For instructions how to configure your package manager to be able to install
the metapackages, see
<https://computing.docs.ligo.org/guide/software/installation/>.
""")  # noqa: E501

METAPACKAGE_PAGE_TEMPLATE = jinja2.Template("""---
title: {{ name }}
---
# `{{ name }}`

**License:** [GPL-3.0-or-later](https://spdx.org/licenses/GPL-3.0-or-later.html)  
**Maintainer:** {{ maintainer }}  
**Priority:** {{ priority }}  
**Section:** {{ section }}  
**Summary:** {{ desc_short }}  

## Description

{{ desc_long }}

## Contents

{% for mgr in contents -%}
### {{ PACKAGE_MANAGERS[mgr] }}

**Metapackage name:** `{{ names[mgr] }}`  
{% if mgr in extra_headers -%}
**Extra headers:**
```ini
{{ "\n".join(extra_headers[mgr]) }}
```
{% endif %}

**Packages:**

| Package name |
| ------------ |
{%- for pkg in contents[mgr] %}
| `{{ pkg }}` |{% endfor %}

{% endfor %}

## Tests

The following test commands are automatically run during continuous integration
to validate this metapackage works as advertised:

```bash
{% for item in tests %}
{{ item }}{% endfor %}
```

## Changelog

{% for item in changelog %}
### {{ item.version }}

**Date:** {{ item.date }}  
**Author:** {{ item.author }}  
**Changes**
{% for change in item.changes %}
- {{ change }}{% endfor %}
{% endfor %}
""")  # noqa: E501,W291
METAPACKAGE_PAGE_TEMPLATE.globals = {
    "PACKAGE_MANAGERS": PACKAGE_MANAGERS,
}

FORMATTING = {
    re.compile(r"(<[\w\.@]+>)"): r"(\1)",
    re.compile(r"(http(s)?://[\S+]+)"): r"<\1>",
}


def create_parser():
    """Create an `argparse.ArgumentParser` for this tool
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "metapackage-directory",
        type=Path,
        help="path to metapackages directory",
    )
    parser.add_argument(
        "output-directory",
        type=Path,
        help="target path for output directory",
    )
    return parser


def write_mkdocs_yml(pkgfiles, outfile):
    """Render the `mkdocs.yml` for the given list of metapackage files
    """
    tmplt = outfile.with_suffix(".yml.in")
    metapages = sorted(x.with_suffix('.md').name for x in pkgfiles)
    with open(tmplt, "r") as tmplf:
        mkconf = yaml.load(tmplf)
    mkconf['nav'].append({"Metapackages": metapages})
    with open(outfile, "w") as ymlf:
        yaml.dump(mkconf, ymlf)


def write_index_md(metas, outfile):
    """Write the top-level `index.md` documentation page.
    """
    content = INDEX_TEMPLATE.render(metapackages=metas.values())
    with open(outfile, "w") as outf:
        outf.write(content)


def parse_metapackages(files):
    """Parse all of the metapackage files
    """
    return {f: parse_metapackage(f) for f in sorted(files)}


def parse_metapackage(metafile):
    """Parse the given metapackage YAML file

    This returns a slightly modified version of the original YAML file
    with some extra keys to help with documentation rendering.
    """
    # read the file with some formatting substitutions
    with open(metafile, "r") as inf:
        text = inf.read()
    for regex, repl in FORMATTING.items():
        text = regex.sub(repl, text)
    meta = yaml.load(text)

    # post-process
    meta["name"] = metafile.stem
    meta["changelog"].sort(key=itemgetter("date"), reverse=True)

    meta["contents"] = {
        mgr: sorted(generate._get_dependencies(meta, mgr))
        for mgr in PACKAGE_MANAGERS
        if mgr not in meta.get("skip", [])
    }
    meta["names"] = {
        mgr: generate.get_package_name(meta, mgr, meta["name"])
        for mgr in PACKAGE_MANAGERS
        if mgr not in meta.get("skip", [])
    }
    # make sure the following keys are present
    for key, default in (
        ("extra_headers", dict),
    ):
        meta.setdefault(key, default())
    return meta


def write_metapackage_md(meta, outfile):
    """Write the given metapackage mapping to markdown
    """
    content = METAPACKAGE_PAGE_TEMPLATE.render(**meta)
    with open(outfile, "w") as outf:
        outf.write(content)


def find_metapackages(metadir):
    """Find all of the metapackages in the given directory

    Just a dumb glob of all `*.yml` files.
    """
    return Path(metadir).glob("*.yml")


def make_docs(args=None):
    """Generate the documentation website for this metapackage repo

    Steps:

    - find all of the metapackages and parse them
    - write a top-level MKDocs configuration file
    - write the top-level `index.md` docs file
    - write a `<metapackage>.md` docs file for each metapackage
    """
    parser = create_parser()
    args = parser.parse_args(args=args)
    metadir = getattr(args, "metapackage-directory")
    outdir = getattr(args, "output-directory")
    docsdir = outdir / "docs"
    docsdir.mkdir(parents=True, exist_ok=True)

    # find metapackages
    metapackagefiles = list(find_metapackages(metadir))

    # parse metapackages
    metapackages = parse_metapackages(metapackagefiles)

    # write the mkdocs file
    write_mkdocs_yml(
        metapackagefiles,
        outdir / "mkdocs.yml",
    )
    write_index_md(
        metapackages,
        docsdir / "index.md",
    )
    # write a page for each page
    for path, meta in metapackages.items():
        outfile = docsdir / path.with_suffix('.md').name
        write_metapackage_md(meta, outfile)


# run the thing from the command-line
if __name__ == "__main__":
    make_docs()
