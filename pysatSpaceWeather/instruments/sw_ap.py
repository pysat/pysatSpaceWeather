#!/usr/bin/env python
# -*- coding: utf-8 -*-.
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
#
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
"""Supports ap index values.

Properties
----------
platform
    'sw'
name
    'ap'
tag
    - 'def' Definitive ap data from GFZ
    - 'now' Nowcast ap data from GFZ
    - 'prediction' Predictions from SWPC for the next 3 days
    - 'forecast' Forecast data from SWPC (next 3 days)
    - 'recent' The last 30 days of Ap data from SWPC
    - '45day' 45-Day forecast data from the Air Force
inst_id
    - ''

Note
----
Downloads data from ftp.gfz-potsdam.de or SWPC. These files also contain Kp
data (with the GFZ data additionally containing Cp data), and so the additional
data files will be saved to the appropriate data directories to avoid multiple
downloads.

The historic definitive and nowcast Kp files are stored in yearly files, with
the current year being updated remotely on a regular basis.  If you are using
historic data for the current year, we recommend re-downloading it before
performing your data processing.

The forecast data is stored by generation date, where each file contains the
forecast for the next three days, the observed daily Ap from the prior day, and
the estimated Ap from the current day. Forecast data downloads are only
supported for the current day. When loading forecast data, the date specified
with the load command is the date the forecast was generated. The data loaded
will span three days. To always ensure you are loading the most recent data,
load the data with tomorrow's date.

Recent data is also stored by the generation date from the SWPC. Each file
contains 30 days of Ap measurements. The load date issued to pysat corresponds
to the generation date.

Examples
--------
::

    ap = pysat.Instrument('sw', 'ap', tag='recent')
    ap.download()
    ap.load(date=ap.tomorrow())


Warnings
--------
The 'forecast', 'recent', and '45day' tags load Ap data for a specific period of
time. Loading multiple files, loading multiple days, the data padding feature,
and multi_file_day feature available from the pyast.Instrument object is not
appropriate for this tag data.

"""

import datetime as dt
import numpy as np
import pandas as pds

import pysat

from pysatSpaceWeather.instruments import methods

# ----------------------------------------------------------------------------
# Instrument attributes

platform = 'sw'
name = 'ap'
tags = {'def': 'Definitive Kp data from GFZ',
        'now': 'Nowcast Kp data from GFZ',
        'prediction': 'SWPC Predictions for the next three days',
        'forecast': 'SWPC Forecast data: prior day to three days hence',
        'recent': 'SWPC provided Kp for past 30 days',
        '45day': 'Air Force 45-day Forecast'}
inst_ids = {'': list(tags.keys())}

# Generate todays date to support loading forecast data
now = dt.datetime.utcnow()
today = dt.datetime(now.year, now.month, now.day)
tomorrow = today + dt.timedelta(days=1)

# ----------------------------------------------------------------------------
# Instrument test attributes

# Set test dates
_test_dates = {'': {'def': dt.datetime(2009, 1, 1),
                    'now': dt.datetime(2020, 1, 1),
                    'forecast': tomorrow,
                    'prediction': tomorrow,
                    'recent': today,
                    '45day': today}}

# ----------------------------------------------------------------------------
# Instrument methods

preprocess = methods.general.preprocess


def init(self):
    """Initialize the Instrument object with instrument specific values."""

    self.acknowledgements = methods.kp_ap.acknowledgements(self.name, self.tag)
    self.references = methods.kp_ap.references(self.name, self.tag)
    pysat.logger.info(self.acknowledgements)
    return


def clean(self):
    """Clean the Kp, not required for this index (empty function)."""

    return


# ----------------------------------------------------------------------------
# Instrument functions


def load(fnames, tag='', inst_id=''):
    """Load Ap index files.

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
    result : pandas.DataFrame
        Object containing satellite data
    meta : pysat.Meta
        Object containing metadata such as column names and units

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """

    meta = pysat.Meta()
    if tag in ['def', 'now']:
        # Load the definitive or nowcast data. The Ap data stored in yearly
        # files, and we need to return data daily.  The daily date is
        # attached to filename.  Parse off the last date, load month of data,
        # and downselect to the desired day
        result = methods.gfz.load_def_now(fnames)

        # Initalize the meta data
        fill_val = np.nan
        for kk in result.keys():
            if kk.lower().find('ap') >= 0:
                methods.kp_ap.initialize_ap_metadata(meta, kk, fill_val)
            elif kk.find('Bartels') >= 0:
                methods.kp_ap.initialize_bartel_metadata(meta, kk)
    else:
        # Load the forecast, recent, prediction, or 45day data
        all_data = []
        for fname in fnames:
            result = pds.read_csv(fname, index_col=0, parse_dates=True)
            all_data.append(result)

        result = pds.concat(all_data)
        fill_val = -1

        # Initalize the meta data
        for kk in result.keys():
            methods.kp_ap.initialize_ap_metadata(meta, kk, fill_val)

    return result, meta


def list_files(tag='', inst_id='', data_path='', format_str=None):
    """List local files for the requested Instrument tag.

    Parameters
    -----------
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
    files : pysat._files.Files
        A class containing the verified available files

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """

    if tag in ['def', 'now']:
        files = methods.gfz.kp_ap_cp_list_files(name, tag, inst_id, data_path,
                                                format_str=format_str)
    else:
        files = methods.swpc.list_files(name, tag, inst_id, data_path,
                                        format_str=format_str)

    return files


def download(date_array, tag, inst_id, data_path, mock_download_dir=None):
    """Download the Ap index data from the appropriate repository.

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
    mock_download_dir : str or NoneType
        Local directory with downloaded files or None. If not None, will
        process any files with the correct name and date as if they were
        downloaded (default=None)

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    Warnings
    --------
    Only able to download current recent data, not archived forecasts.

    Raises
    ------
    IOError
        If an unknown mock download directory is supplied.

    """

    if tag in ['def', 'now']:
        methods.gfz.kp_ap_cp_download(platform, name, date_array, tag, inst_id,
                                      data_path, mock_download_dir)
    elif tag == 'recent':
        methods.swpc.kp_ap_recent_download(name, date_array, data_path,
                                           mock_download_dir)
    elif tag == 'forecast':
        methods.swpc.geomag_forecast_download(name, date_array, data_path,
                                              mock_download_dir)
    elif tag == 'prediction':
        methods.swpc.solar_geomag_predictions_download(
            name, date_array, data_path, mock_download_dir)
    else:
        methods.swpc.recent_ap_f107_download(name, date_array, data_path,
                                             mock_download_dir)

    return
