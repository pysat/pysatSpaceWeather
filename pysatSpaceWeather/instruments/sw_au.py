# -*- coding: utf-8 -*-
"""Supports the auroral electrojet AU values.

Properties
----------
platform
    'sw'
name
    'au'
tag
    - 'lasp' Predicted AU from real-time ACE or DSCOVR provided by LASP
inst_id
    - ''

"""

import datetime as dt
import numpy as np

import pysat

from pysatSpaceWeather.instruments.methods import auroral_electrojet as mm_ae
from pysatSpaceWeather.instruments.methods import lasp

# ----------------------------------------------------------------------------
# Instrument attributes

platform = 'sw'
name = 'au'
tags = {'lasp': 'Predicted AU from real-time ACE or DSCOVR provided by LASP'}
inst_ids = {'': [tag for tag in tags.keys()]}

# Generate today's date to support loading predicted data sets
today = pysat.utils.time.today()
tomorrow = today + dt.timedelta(days=1)

# ----------------------------------------------------------------------------
# Instrument test attributes

_test_dates = {'': {'lasp': today}}

# ----------------------------------------------------------------------------
# Instrument methods


def init(self):
    """Initialize the Instrument object with instrument specific values."""

    self.acknowledgements = mm_ae.acknowledgements(self.name, self.tag)
    self.references = mm_ae.references(self.name, self.tag)
    pysat.logger.info(self.acknowledgements)
    return


def clean(self):
    """Clean the AU index, empty function."""
    return


# ----------------------------------------------------------------------------
# Instrument functions


def load(fnames, tag='', inst_id=''):
    """Load the AU index files.

    Parameters
    ----------
    fnames : pandas.Series
        Series of filenames
    tag : str
        Instrument tag string. (default='')
    inst_id : str
        Instrument ID, not used. (default='')

    Returns
    -------
    data : pandas.DataFrame
        Object containing satellite data
    pysat.Meta
        Object containing metadata such as column names and units

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """
    data = pysat.instruments.methods.general.load_csv_data(
        fnames, read_csv_kwargs={'index_col': 0, 'parse_dates': True})

    # Create metadata
    meta = pysat.Meta()
    meta['au'] = {meta.labels.units: 'nT',
                  meta.labels.name: 'AU',
                  meta.labels.notes: tags[tag],
                  meta.labels.desc: ''.join([
                      'Auroral Electrojet upper envelope, best estimate ',
                      'of the average value over the next two hours']),
                  meta.labels.fill_val: np.nan,
                  meta.labels.min_val: 0.0,
                  meta.labels.max_val: np.inf}

    return data, meta


def list_files(tag='', inst_id='', data_path='', format_str=None):
    """List local data files for AU data.

    Parameters
    ----------
    tag : str
        Instrument tag, accepts any value from `tags`. (default='')
    inst_id : str
        Instrument ID, not used. (default='')
    data_path : str
        Path to data directory. (default='')
    format_str : str or NoneType
        User specified file format.  If None is specified, the default
        formats associated with the supplied tags are used. (default=None)

    Returns
    -------
    files : pysat.Files
        A class containing the verified available files

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """
    # Get the format string, if not supplied by the user
    if format_str is None:
        format_str = ''.join(['sw_au_', tag, '_{year:4d}-{month:2d}-',
                              '{day:2d}.txt'])

    # Get the desired files
    files = pysat.Files.from_os(data_path=data_path, format_str=format_str)

    return files


def download(date_array, tag, inst_id, data_path):
    """Download the AU index data from the appropriate repository.

    Parameters
    ----------
    date_array : array-like or pandas.DatetimeIndex
        Array-like or index of datetimes for which files will be downloaded.
    tag : str
        Instrument tag, used to determine download location.
    inst_id : str
        Instrument ID, not used.
    data_path : str
        Path to data directory.

    Raises
    ------
    IOError
        If the data link has an unexpected format

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """
    lasp.prediction_downloads(name, tag, data_path)

    return