#!/usr/bin/env python

"""Utility to order metapackages by dependency, namely with standalone packages first
"""

from pathlib import Path

import networkx

import yaml

metafiles = list(Path("meta").glob("*.yml"))
metapackages = [ymlf.with_suffix("").name for ymlf in metafiles]
graph = networkx.DiGraph()

for yamlfile in metafiles:
    pkg = yamlfile.with_suffix("").name
    graph.add_node(pkg)
    with yamlfile.open("r") as stream:
        meta = yaml.load(stream, Loader=yaml.SafeLoader)
    deps = meta.get("deps", [])
    for key, val in deps.items():
        if key in metapackages and (val is None or val.get("conda", 0) is None):
            graph.add_edge(pkg, key)

order = list(networkx.topological_sort(graph))
order.reverse()
for pkg in order:
    print(pkg)
