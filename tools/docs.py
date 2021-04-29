#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Generate a docs page for the LSCSoft Metpackages
"""

import argparse
import re
from operator import itemgetter
from pathlib import Path

import jinja2

import yaml

import generate

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

The available metapackages are:

| Package name | Description |
| ------------ | ----------- |
{%- for pkg in metapackages %}
| [`{{ pkg['name'] }}`]({{ pkg['name'] }}.md) | {{ pkg['desc_short'] }} |{% endfor %}

For instructions how to configure your package manager to be able to install
the metapackages, see
<https://computing.docs.ligo.org/guide/software/installation/>.
""")

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
""")
METAPACKAGE_PAGE_TEMPLATE.globals = {
    "PACKAGE_MANAGERS": PACKAGE_MANAGERS,
}

FORMATTING = {
    re.compile(r"(<[\w\.@]+>)"): r"(\1)",
    re.compile(r"(http(s)?://[\S+]+)"): r"<\1>",
}


def create_parser():
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
    tmplt = outfile.with_suffix(".yml.in")
    metapages = sorted(x.with_suffix('.md').name for x in pkgfiles)
    with open(tmplt, "r") as tmplf:
        mkconf = yaml.load(tmplf, Loader=yaml.SafeLoader)
    mkconf['nav'].append({"Metapackages": metapages})
    with open(outfile, "w") as ymlf:
        yaml.dump(mkconf, ymlf)


def write_index_md(metas, outfile):
    content = INDEX_TEMPLATE.render(metapackages=metas.values())
    with open(outfile, "w") as outf:
        outf.write(content)


def parse_metapackages(files):
    return {f: parse_metapackage(f) for f in sorted(files)}


def parse_metapackage(metafile):
    # read the file with some formatting substitutions
    with open(metafile, "r") as inf:
        text = inf.read()
    for regex, repl in FORMATTING.items():
        text = regex.sub(repl, text)
    meta = yaml.safe_load(text)

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
    return meta


def write_metapackage_md(meta, outfile):
    content = METAPACKAGE_PAGE_TEMPLATE.render(**meta)
    with open(outfile, "w") as outf:
        outf.write(content)


def find_metapackages(metadir):
    return Path(metadir).glob("*.yml")


def make_docs(args=None):
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


if __name__ == "__main__":
    make_docs()
