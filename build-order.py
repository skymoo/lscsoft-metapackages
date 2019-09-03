#!/usr/bin/env python

"""Utility to order metapackages by dependency, namely with standalone packages first
"""

import argparse
from pathlib import Path

import networkx

import yaml

parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    "build",
    choices=["conda", "deb", "rpm"],
    default="conda",
    nargs="?",
    help="type of build",
)
args = parser.parse_args()

# find all of the metapackages and get a list of their names
metafiles = list(Path("meta").glob("*.yml"))
metapackages = [ymlf.with_suffix("").name for ymlf in metafiles]

graph = networkx.DiGraph()

for yamlfile in metafiles:
    # parse metapackage definition
    pkg = yamlfile.with_suffix("").name
    with yamlfile.open("r") as stream:
        meta = yaml.load(stream, Loader=yaml.SafeLoader)

    # if metapackage is skipped for this build, continue
    if args.build in meta.get('skip', []):
        continue

    # otherwise, store the metapackage
    graph.add_node(pkg)

    # if this has dependencies on other metapackages, store them as edges
    deps = meta.get("deps", [])
    for key, val in deps.items():
        if key in metapackages and (val is None or val.get(args.build, 0) is None):
            graph.add_edge(pkg, key)

# sort the graph to resolve the correct build order
order = list(networkx.topological_sort(graph))
order.reverse()


for pkg in order:
    print(pkg)
