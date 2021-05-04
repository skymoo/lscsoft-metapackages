#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2021 Cardiff University
# This document is placed into the public domain

"""Configure the tests for IGWN metapackages
"""

__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"

from pathlib import Path

import pytest


def metapackage_name_from_script_path(path):
    return Path(path).parent.parent.name


def pytest_addoption(parser):
    parser.addoption(
        "--script",
        nargs="+",
        default=[],
        help="path to test script to run",
    )


def pytest_generate_tests(metafunc):
    if "script" in metafunc.fixturenames:
        scripts = metafunc.config.getoption("script")
        metafunc.parametrize("script", [
            pytest.param(scrpt, id=metapackage_name_from_script_path(scrpt))
            for scrpt in scripts
        ])
