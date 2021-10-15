"""Initialization file for pysatSpaceWeather module."""

import os

from pysatSpaceWeather import instruments  # noqa F401

# Set directory for test data
proj_dir = os.path.abspath(os.path.dirname(__file__))
test_data_path = os.path.join(proj_dir, 'tests', 'test_data')

# Set the package version
with open(os.path.join(proj_dir, "version.txt"), "r") as fin:
    __version__ = fin.read().strip()

# Clean up
del proj_dir, fin
