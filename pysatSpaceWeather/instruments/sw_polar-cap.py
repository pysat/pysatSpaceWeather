# -*- coding: utf-8 -*-
"""Supports polar cap indexes.

Properties
----------
platform
    'sw'
name
    'polar-cap'
tag
    - 'prediction' Predictions from SWPC for the next 3 days
inst_id
    ''

Note
----
Downloads data from SWPC. These files also contain other data indices, and so
the additional data files will be saved to the appropriate data directories to
avoid multiple downloads.

The forecast/prediction data is stored by generation date, where each file
contains the forecast for the next three days. Forecast data downloads are only
supported for the current day. When loading forecast data, the date specified
with the load command is the date the forecast was generated. The data loaded
will span three days. To always ensure you are loading the most recent data,
load the data with tomorrow's date.

Examples
--------
::

    pc = pysat.Instrument('sw', 'polar-cap', tag='prediction')
    pc.download()
    pc.load(date=pc.tomorrow())


Warnings
--------
The 'prediction' tag loads polar cap absoprtion predictions for a specific
period of time. Loading multiple files, loading multiple days, the data padding
feature, and multi_file_day feature available from the pyast.Instrument object
is not appropriate for these tags data.

"""

import datetime as dt
import functools
import numpy as np
import pandas as pds

import pysat

from pysatSpaceWeather.instruments import methods

# ----------------------------------------------------------------------------
# Instrument attributes

platform = 'sw'
name = 'polar-cap'
tags = {'prediction': 'SWPC Predictions for the next three days'}
inst_ids = {'': list(tags.keys())}

# Generate todays date to support loading forecast data
now = dt.datetime.utcnow()
today = dt.datetime(now.year, now.month, now.day)
tomorrow = today + dt.timedelta(days=1)

# ----------------------------------------------------------------------------
# Instrument test attributes

# Set test dates
_test_dates = {'': {'prediction': tomorrow}}

# ----------------------------------------------------------------------------
# Instrument methods

preprocess = methods.general.preprocess


def init(self):
    """Initialize the Instrument object with instrument specific values."""

    self.acknowledgements = methods.swpc.ackn
    self.references = "".join(["Check SWPC for appropriate references: ",
                               "https://www.swpc.noaa.gov/phenomena"])
    pysat.logger.info(self.acknowledgements)
    return


def clean(self):
    """Clean the polar cap indexes, not required (empty function)."""

    return


# ----------------------------------------------------------------------------
# Instrument functions

list_files = functools.partial(methods.swpc.list_files, name)


def load(fnames, tag='', inst_id=''):
    """Load storm probability files.

    Parameters
    ----------
    fnames : pandas.Series
        Series of filenames
    tag : str
        Instrument tag (default='')
    inst_id : str
        Instrument ID, not used. (default='')

    Returns
    -------
    data : pandas.DataFrame
        Object containing satellite data
    meta : pysat.Meta
        Object containing metadata such as column names and units

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    Warnings
    --------
    tag '' has been deprecated, will be removed in version 0.2.0+

    """

    # Load the data
    all_data = []
    for fname in fnames:
        result = pds.read_csv(fname, index_col=0, parse_dates=True)
        all_data.append(result)

    data = pds.concat(all_data)

    # Initialize the metadata
    meta = pysat.Meta()
    for lkey in ['fill_val', 'min_val', 'max_val']:
        meta.labels.label_type[lkey] = (float, int, np.float64, np.int64, str)

    for dkey in data.columns:
        meta[dkey] = {meta.labels.units: '',
                      meta.labels.name: dkey,
                      meta.labels.desc: dkey.replace('_', ' '),
                      meta.labels.min_val: 'green',
                      meta.labels.max_val: 'red',
                      meta.labels.fill_val: ''}

    return data, meta


def download(date_array, tag, inst_id, data_path):
    """Download the polar cap indices from the appropriate repository.

    Parameters
    ----------
    date_array : array-like or pandas.DatetimeIndex
        Array-like or index of datetimes to be downloaded.
    tag : str
        Denotes type of file to load.
    inst_id : str
        Specifies the instrument identification, not used.
    data_path : str
        Path to data directory.

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    Warnings
    --------
    Only able to download current recent data, not archived forecasts.

    """

    if tag == 'prediction':
        methods.swpc.solar_geomag_predictions_download(name, date_array,
                                                       data_path)

    return