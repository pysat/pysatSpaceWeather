"""Core library for pysatSpaceWeather."""

try:
    from importlib import metadata
    from importlib import resources
except ImportError:
    import importlib_metadata as metadata
    import importlib-resources as resources

from pysatSpaceWeather import instruments  # noqa F401

__version__ = metadata.version('pysatSpaceWeather')
test_data_path = str(resources.path(__package__, 'tests',
                                    'test_data').__enter__())
