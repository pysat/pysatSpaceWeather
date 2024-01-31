#!/usr/bin/env python
# -*- coding: utf-8 -*-.
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
#
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
"""Supports Sunspot Number (SSN) and related indices.

Properties
----------
platform
    'sw'
name
    'ssn'
tag
    - 'prelim' Preliminary SWPC daily solar indices
    - 'daily' Daily SWPC solar indices (contains last 30 days)
    - 'now' Nowcast and definitive international sunspot number data from GFZ

Examples
--------
Download and load some preliminary SSN data.
::

    ssn = pysat.Instrument('sw', 'ssn', tag='prelim')
    ssn.download(start=dt.datetime(2001, 1, 1))
    ssn.load(date=dt.datetime(2001, 1, 1))

"""

import datetime as dt
import numpy as np
import os
import pandas as pds

import pysat

from pysatSpaceWeather.instruments import methods

# ----------------------------------------------------------------------------
# Instrument attributes

platform = 'sw'
name = 'ssn'
tags = {'prelim': 'Preliminary SWPC daily solar indices',
        'daily': 'Daily SWPC solar indices (contains last 30 days)',
        'now':
        'Nowcast and definitive international sunspot number data from GFZ'}

# Dict keyed by inst_id that lists supported tags for each inst_id
inst_ids = {'': [tag for tag in tags.keys()]}

# Dict keyed by inst_id that lists supported tags and a good day of test data
# generate todays date to support loading forecast data
now = dt.datetime.utcnow()
today = dt.datetime(now.year, now.month, now.day)
tomorrow = today + pds.DateOffset(days=1)

# ----------------------------------------------------------------------------
# Instrument test attributes

_test_dates = {'': {'prelim': dt.datetime(2009, 1, 1),
                    'now': dt.datetime(2009, 1, 1),
                    'daily': tomorrow}}

# Other tags assumed to be True
_test_download_ci = {'': {'prelim': False}}

# ----------------------------------------------------------------------------
# Instrument methods

preprocess = methods.general.preprocess


def init(self):
    """Initialize the Instrument object with instrument specific values."""

    # Set the required Instrument attributes
    if self.tag == 'now':
        self.acknowledgements = methods.gfz.ackn
    else:
        self.acknowledgements = methods.swpc.ackn
    self.references = "".join(["E.g., Arlt, R., Vaquero, J.M. Historical ",
                               "sunspot records. Living Rev Sol Phys 17, 1 ",
                               '(2020). doi:10.1007/s41116-020-0023-y'])
    pysat.logger.info(self.acknowledgements)

    return


def clean(self):
    """Clean the data, empty function as this is not necessary."""

    return


# ----------------------------------------------------------------------------
# Instrument functions


def load(fnames, tag='', inst_id=''):
    """Load SSN files.

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

    """

    # Get the desired file dates and file names from the daily indexed list
    file_dates = list()
    if tag in ['prelim', 'now']:
        unique_files = list()
        for fname in fnames:
            file_dates.append(dt.datetime.strptime(fname[-10:], '%Y-%m-%d'))
            if fname[0:-11] not in unique_files:
                unique_files.append(fname[0:-11])
        fnames = unique_files

    # Load the CSV data files
    data = pysat.instruments.methods.general.load_csv_data(
        fnames, read_csv_kwargs={"index_col": 0, "parse_dates": True})

    # Adjust variable names to be consistent across data sets
    if tag == 'now':
        data = data.rename(columns={'SN': 'ssn'})

    # If there is a date range, downselect here
    if len(file_dates) > 0:
        idx, = np.where((data.index >= min(file_dates))
                        & (data.index < max(file_dates) + dt.timedelta(days=1)))
        data = data.iloc[idx, :]

    # Initialize the metadata
    meta = pysat.Meta()
    meta['ssn'] = {meta.labels.units: '',
                   meta.labels.name: 'Sunspot Number',
                   meta.labels.notes: '',
                   meta.labels.desc: 'SESC Sunspot Number',
                   meta.labels.fill_val: -999,
                   meta.labels.min_val: 0,
                   meta.labels.max_val: np.inf}
    if 'ss_area' in data.columns:
        meta['ss_area'] = {meta.labels.units: '10$^-6$ Solar Hemisphere',
                           meta.labels.name: 'Sunspot Area',
                           meta.labels.notes: '',
                           meta.labels.desc:
                           ''.join(['Sunspot Area in Millionths of the ',
                                    'Visible Hemisphere']),
                           meta.labels.fill_val: -999,
                           meta.labels.min_val: 0,
                           meta.labels.max_val: 1.0e6}
    if 'new_reg' in data.columns:
        meta['new_reg'] = {meta.labels.units: '',
                           meta.labels.name: 'New Regions',
                           meta.labels.notes: '',
                           meta.labels.desc: 'New active solar regions',
                           meta.labels.fill_val: -999,
                           meta.labels.min_val: 0,
                           meta.labels.max_val: np.inf}

    return data, meta


def list_files(tag='', inst_id='', data_path='', format_str=None):
    """List local solar magnetic field data files.

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
    out_files : pysat._files.Files
        A class containing the verified available files

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """

    if tag == 'prelim':
        # Files are by year (and quarter)
        if format_str is None:
            format_str = ''.join(['ssn_prelim_{year:04d}_{month:02d}',
                                  '_v{version:01d}.txt'])
        out_files = pysat.Files.from_os(data_path=data_path,
                                        format_str=format_str)

        if not out_files.empty:
            # Set each file's valid length at a 1-day resolution
            orig_files = out_files.sort_index().copy()
            new_files = list()

            for orig in orig_files.items():
                # Version determines each file's valid length
                version = int(orig[1].split("_v")[1][0])
                doff = pds.DateOffset(years=1) if version == 2 \
                    else pds.DateOffset(months=3)
                istart = orig[0]
                iend = istart + doff - pds.DateOffset(days=1)

                # Ensure the end time does not extend past the number of
                # possible days included based on the file's download time
                fname = os.path.join(data_path, orig[1])
                dend = dt.datetime.utcfromtimestamp(os.path.getctime(fname))
                dend = dend - pds.DateOffset(days=1)
                if dend < iend:
                    iend = dend

                # Pad the original file index
                out_files.loc[iend] = orig[1]
                out_files = out_files.sort_index()

                # Save the files at a daily cadence over the desired period
                new_files.append(out_files.loc[istart:
                                               iend].asfreq('D', 'pad'))
            # Add the newly indexed files to the file output
            out_files = pds.concat(new_files, sort=True)
            out_files = out_files.dropna()
            out_files = out_files.sort_index()
            out_files = out_files + '_' + out_files.index.strftime('%Y-%m-%d')

    elif tag == 'now':
        if format_str is None:
            format_str = 'SN_{year:04d}-{month:02d}.txt'

        out_files = pysat.Files.from_os(data_path=data_path,
                                        format_str=format_str)
        if not out_files.empty:
            freq = pds.DateOffset(months=1, days=-1)
            out_files.loc[out_files.index[-1] + freq] = out_files.iloc[-1]
            out_files = out_files.asfreq('D', 'pad')
            out_files = out_files + '_' + out_files.index.strftime('%Y-%m-%d')

    elif tag == 'daily':
        out_files = methods.swpc.list_files(name, tag, inst_id, data_path,
                                            format_str=format_str)

    return out_files


def download(date_array, tag, inst_id, data_path, update_files=False,
             mock_download_dir=None):
    """Download solar magnetic field data from the appropriate repository.

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
        Re-download data for files that already exist if True. (default=False)
    mock_download_dir : str or NoneType
        Local directory with downloaded files or None. If not None, will
        process any files with the correct name and date as if they were
        downloaded. (default=None)

    Raises
    ------
    IOError
        If a problem is encountered connecting to the gateway or retrieving
        data from the remote or local repository.

    Warnings
    --------
    Only able to download current forecast data, not archived forecasts.

    """
    if tag == 'prelim':
        # Get the local files, to ensure that the version 1 files are
        # downloaded again if more data has been added
        local_files = list_files(tag, inst_id, data_path)

        methods.swpc.old_indices_dsd_download(name, date_array, data_path,
                                              local_files, today,
                                              mock_download_dir)

    elif tag == 'daily':
        methods.swpc.daily_dsd_download(name, today, data_path,
                                        mock_download_dir)

    elif tag == 'now':
        # Set the download input options
        gfz_data_name = 'SN'
        local_file_prefix = '{:s}_'.format(gfz_data_name)

        # Call the download routine
        methods.gfz.json_downloads(date_array, data_path, local_file_prefix,
                                   "%Y-%m", gfz_data_name,
                                   pds.DateOffset(months=1, seconds=-1),
                                   update_files=update_files,
                                   mock_download_dir=mock_download_dir)

    return
