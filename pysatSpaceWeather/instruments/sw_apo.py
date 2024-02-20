#!/usr/bin/env python
# -*- coding: utf-8 -*-.
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
#
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
"""Supports apo index values.

Properties
----------
platform
    'sw'
name
    'apo'
tag
    - 'now' Near real-time nowcast apo data from GFZ
inst_id
    - '30min' Half-hourly indices
    - '60min' Hourly indices

Note
----
Downloads data from ftp.gfz-potsdam.de

Examples
--------
::

    ap30 = pysat.Instrument('sw', 'apo', tag='now', inst_id='30min')
    ap30.download(2009, 1)
    ap30.load(yr=2009, doy=1)

"""

import datetime as dt
import numpy as np
import pandas as pds

import pysat

from pysatSpaceWeather.instruments import methods

# ----------------------------------------------------------------------------
# Instrument attributes

platform = 'sw'
name = 'apo'
tags = {'now': 'Near real-time nowcast apo data from GFZ'}
inst_ids = {inst_id: list(tags.keys()) for inst_id in ['30min', '60min']}

# ----------------------------------------------------------------------------
# Instrument test attributes

# Set test dates
_test_dates = {inst_id: {tag: dt.datetime(2009, 1, 1)
                         for tag in inst_ids[inst_id]}
               for inst_id in inst_ids.keys()}

# ----------------------------------------------------------------------------
# Instrument methods

preprocess = methods.general.preprocess


def init(self):
    """Initialize the Instrument object with instrument specific values."""

    self.acknowledgements = methods.gfz.ackn
    self.references = methods.gfz.hpo_refs
    pysat.logger.info(self.acknowledgements)
    return


def clean(self):
    """Clean the Kp, not required for this index (empty function)."""

    return


# ----------------------------------------------------------------------------
# Instrument functions


def load(fnames, tag='', inst_id=''):
    """Load apo index files.

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

    # Load the nowcast data. The Hpo data is stored in monthly files, and we
    # need to return data daily.  The daily date is attached to filename.
    # Parse off the last date, load month of data, and downselect to the
    # desired day
    result = methods.gfz.load_def_now(fnames)

    # Initalize the meta data
    dkey = 'Hp{:s}'.format(inst_id.split('min')[0])
    meta = pysat.Meta()
    meta[dkey] = {meta.labels.units: '',
                  meta.labels.name: dkey,
                  meta.labels.desc:
                  "{:s}ourly Planetary Open linear index".format(
                      'H' if inst_id == '60min' else 'Half-h'),
                  meta.labels.min_val: 0,
                  meta.labels.max_val: np.inf,
                  meta.labels.fill_val: np.nan}

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

    if format_str is None:
        format_str = 'ap{:s}_{{year:04d}}-{{month:02d}}.txt'.format(
            inst_id.split('min')[0])

    # Files are stored by month, going to add a date to the monthly filename for
    # each day of month.  The load routine will load the year and use the append
    # date to select out approriate data.
    files = pysat.Files.from_os(data_path=data_path, format_str=format_str)
    if not files.empty:
        files.loc[files.index[-1]
                  + pds.DateOffset(months=1, days=-1)] = files.iloc[-1]
        files = files.asfreq('D', 'pad')
        files = files + '_' + files.index.strftime('%Y-%m-%d')

    return files


def download(date_array, tag, inst_id, data_path, update_files=False,
             mock_download_dir=None):
    """Download the apo index data from the appropriate repository.

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
    update_files : bool
        Re-download data for files that already exist if True (default=False)
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

    # Set the download input options
    gfz_data_name = 'ap{:s}'.format(inst_id.split('min')[0])
    local_file_prefix = '{:s}_'.format(gfz_data_name)
    local_date_fmt = "%Y-%m"
    freq = pds.DateOffset(months=1, seconds=-1)

    # Call the download routine
    methods.gfz.json_downloads(date_array, data_path, local_file_prefix,
                               local_date_fmt, gfz_data_name, freq,
                               update_files=update_files,
                               mock_download_dir=mock_download_dir)

    return
