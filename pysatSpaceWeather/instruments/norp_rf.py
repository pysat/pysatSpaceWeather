#!/usr/bin/env python
# -*- coding: utf-8 -*-.
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
# ----------------------------------------------------------------------------
"""Supports solar radio flux values from the Nobeyama Radio Polarimeters.

Properties
----------
platform
    'norp'
name
    'rf'
tag
    - 'daily' Daily solar flux values from 1951-11-01 onward
inst_id
    - None supported

Examples
--------
Download and load all of the daily radio flux data.
::

    rf = pysat.Instrument('norp', 'rf', tag='daily')
    rf.download(start=dt.datetime(1951, 11, 1), stop=rf.today())
    rf.load(date=dt.datetime(1951, 11, 1), end_date=rf.today())

"""

import datetime as dt
import numpy as np
import pandas as pds

import pysat

from pysatSpaceWeather.instruments import methods

# ----------------------------------------------------------------------------
# Instrument attributes

platform = 'norp'
name = 'rf'
tags = {'daily': 'Daily solar flux values'}
inst_ids = {'': [tag for tag in tags.keys()]}

# ----------------------------------------------------------------------------
# Instrument test attributes

_test_dates = {'': {'daily': dt.datetime(1951, 11, 1)}}

# ----------------------------------------------------------------------------
# Instrument methods

preprocess = methods.general.preprocess


def init(self):
    """Initialize the Instrument object with instrument specific values."""

    # Set the required Instrument attributes
    self.acknowledgements = methods.norp.acknowledgements()
    self.references = methods.norp.references(self.name, self.tag)
    pysat.logger.info(self.acknowledgements)

    return


def clean(self):
    """Clean the solar radio flux, empty function as this is not necessary."""

    return


# ----------------------------------------------------------------------------
# Instrument functions


def load(fnames, tag='', inst_id=''):
    """Load NoRP solar radio flux files.

    Parameters
    ----------
    fnames : pandas.Series
        Series of filenames.
    tag : str
        Instrument tag. (default='')
    inst_id : str
        Instrument ID, not used. (default='')

    Returns
    -------
    data : pandas.DataFrame
        Object containing satellite data.
    meta : pysat.Meta
        Object containing metadata such as column names and units.

    See Also
    --------
    pysat.instruments.methods.general.load_csv_data

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """

    # Get the desired file dates and file names from the daily indexed list
    file_dates = list()
    if tag in ['daily']:
        unique_files = list()
        for fname in fnames:
            file_dates.append(dt.datetime.strptime(fname[-10:], '%Y-%m-%d'))
            if fname[0:-11] not in unique_files:
                unique_files.append(fname[0:-11])
        fnames = unique_files

    # Load the CSV data files
    data = pysat.instruments.methods.general.load_csv_data(
        fnames, read_csv_kwargs={"index_col": 0, "parse_dates": True})

    # If there is a date range, downselect here
    if len(file_dates) > 0:
        idx, = np.where((data.index >= min(file_dates))
                        & (data.index < max(file_dates) + dt.timedelta(days=1)))
        data = data.iloc[idx, :]

    # Initialize the metadata
    meta = pysat.Meta()
    for col in data.columns:
        meta[col] = {
            meta.labels.units: 'SFU', meta.labels.notes: '',
            meta.labels.name: 'NoRP solar sadio flux {:} w/AU corr'.format(
                col.replace("_", " ")),
            meta.labels.desc: ''.join([
                'NoRP solar radio flux at ', col.replace("_", " "),
                ' with Astronomical Unit (AU) correction in Solar Flux Units',
                ' (SFU).']),
            meta.labels.fill_val: np.nan,
            meta.labels.min_val: 0, meta.labels.max_val: np.inf}

    return data, meta


def list_files(tag='', inst_id='', data_path='', format_str=None):
    """List local NoRP solar radio flux data files.

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
    out_files : pds.Series
        A Series containing the verified available files

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """
    # Files are by month, going to add date to monthly filename for each day of
    # the month. The load routine will load a month of data and use the
    # appended date to select out appropriate data.
    if format_str is None:
        format_str = "_".join(["norp", "rf", tag, '{year:04d}-{month:02d}.txt'])

    out_files = pysat.Files.from_os(data_path=data_path, format_str=format_str)
    if not out_files.empty:
        out_files.loc[out_files.index[-1] + pds.DateOffset(months=1)
                      - pds.DateOffset(days=1)] = out_files.iloc[-1]
        out_files = out_files.asfreq('D', 'pad')
        out_files = out_files + '_' + out_files.index.strftime('%Y-%m-%d')

    return out_files


def download(date_array, tag, inst_id, data_path, update_files=False,
             mock_download_dir=None):
    """Download NoRP solar radio flux data.

    Parameters
    ----------
    date_array : array-like
        Sequence of dates for which files will be downloaded.
    tag : str
        Denotes type of file to load.
    inst_id : str
        Specifies the satellite ID for a constellation.
    data_path : str
        Path to data directory.
    update_files : bool
        Re-download data for files that already exist if True (default=False)
    mock_download_dir : str or NoneType
        Local directory with downloaded files or None. If not None, will
        process any files with the correct name and date as if they were
        downloaded (default=None)

    Raises
    ------
    IOError
        If a problem is encountered connecting to the gateway or retrieving
        data from the remote or local repository.

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """
    # Download the daily radio flux data from NoRP, saving data in monthly files
    methods.norp.daily_rf_downloads(data_path,
                                    mock_download_dir=mock_download_dir,
                                    start=date_array[0], stop=date_array[-1])

    return
