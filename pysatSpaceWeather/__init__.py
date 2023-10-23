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
test_data_path = path.join(
    path.split(str(resources.path(__package__, '__init__.py').__enter__()))[0],
    'tests', 'test_data')
