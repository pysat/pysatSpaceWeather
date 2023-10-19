"""Core library for pysatSpaceWeather."""

try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata

from pysatSpaceWeather import instruments  # noqa F401

__version__ = metadata.version('PACKAGENAME')
