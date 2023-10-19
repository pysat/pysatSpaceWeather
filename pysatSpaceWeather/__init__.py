"""Core library for pysatSpaceWeather."""

try:
    from importlib import metadata
    from importlib import resources
except ImportError:
    import importlib_metadata as metadata
    import importlib_resources as resources
from os import path

from pysatSpaceWeather import instruments  # noqa F401

__version__ = metadata.version('pysatSpaceWeather')
test_data_path = str(
    resources.path(__package__, path.join('tests', 'test_data')).__enter__())
