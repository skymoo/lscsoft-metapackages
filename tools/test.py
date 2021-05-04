#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Run the tests for the IGWN metapackages
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

import pytest


def test_metapackage(script):
    proc = subprocess.run(
        "bash {}".format(script),
        check=False,
        shell=True,
        env=os.environ,
    )
    if proc.returncode == 77:  # SKIP
        pytest.skip("skipped")
    proc.check_returncode()


if __name__ == "__main__":
    sys.exit(pytest.main(args=[__file__] + sys.argv[1:]))
