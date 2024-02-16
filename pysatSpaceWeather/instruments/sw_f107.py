#!/usr/bin/env python
# -*- coding: utf-8 -*-.
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
#
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
"""Supports F10.7 index values.

Properties
----------
platform
    'sw'
name
    'f107'
tag
    - 'historic' LASP F10.7 data (downloads by month, loads by day)
    - 'prelim' Preliminary SWPC daily solar indices
    - 'now' A mix of nowcast and definitive values from GFZ
    - 'daily' Daily SWPC solar indices (contains last 30 days)
    - 'forecast' Grab forecast data from SWPC (next 3 days)
    - '45day' 45-Day Forecast data from the Air Force
inst_id
    - '' No distinction, may include observed, adjusted, or both
    - 'obs' Observed F10.7
    - 'adj' Adjusted F10.7

Examples
--------
Download and load all of the historic F10.7 data.  Note that it will not
stop on the current date, but a point in the past when post-processing has
been successfully completed.
::

    f107 = pysat.Instrument('sw', 'f107', tag='historic')
    f107.download(start=f107.lasp_stime, stop=f107.today())
    f107.load(date=f107.lasp_stime, end_date=f107.today())


Note
----
The forecast data is stored by generation date, where each file contains the
forecast for the next three days. Forecast data downloads are only supported
for the current day. When loading forecast data, the date specified with the
load command is the date the forecast was generated. The data loaded will span
three days. To always ensure you are loading the most recent data, load
the data with tomorrow's date.
::

    f107 = pysat.Instrument('sw', 'f107', tag='forecast')
    f107.download()
    f107.load(date=f107.tomorrow())


Warnings
--------
The 'forecast' F10.7 data loads three days at a time. Loading multiple files,
loading multiple days, the data padding feature, and multi_file_day feature
available from the pyast.Instrument object is not appropriate for 'forecast'
data.

Like 'forecast', the '45day' forecast loads a specific period of time (45 days)
and subsequent files contain overlapping data.  Thus, loading multiple files,
loading multiple days, the data padding feature, and multi_file_day feature
available from the pyast.Instrument object is not appropriate for '45day' data.

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
name = 'f107'
tags = {'historic': 'Daily LASP value of F10.7',
        'prelim': 'Preliminary SWPC daily solar indices',
        'now': 'Nowcast and definitive data from GFZ',
        'daily': 'Daily SWPC solar indices (contains last 30 days)',
        'forecast': 'SWPC Forecast F107 data next (3 days)',
        '45day': 'Air Force 45-day Forecast'}

# Dict keyed by inst_id that lists supported tags for each inst_id
inst_ids = {'': [tag for tag in tags.keys() if tag != 'now'], 'obs': ['now'],
            'adj': ['now']}

# Dict keyed by inst_id that lists supported tags and a good day of test data
# generate todays date to support loading forecast data
now = dt.datetime.utcnow()
today = dt.datetime(now.year, now.month, now.day)
tomorrow = today + dt.timedelta(days=1)

# The LASP archive start day is also important
lasp_stime = dt.datetime(1947, 2, 14)

# ----------------------------------------------------------------------------
# Instrument test attributes

_test_dates = {'': {'historic': dt.datetime(2009, 1, 1),
                    'prelim': dt.datetime(2009, 1, 1),
                    'daily': today,
                    'forecast': tomorrow,
                    '45day': today},
               'obs': {'now': dt.datetime(2009, 1, 1)},
               'adj': {'now': dt.datetime(2009, 1, 1)}}

# Other tags assumed to be True
_test_download_ci = {'': {'prelim': False}}

# ----------------------------------------------------------------------------
# Instrument methods

preprocess = methods.general.preprocess


def init(self):
    """Initialize the Instrument object with instrument specific values."""

    # Set the required Instrument attributes
    self.acknowledgements = methods.f107.acknowledgements(self.tag)
    self.references = methods.f107.references(self.tag)
    pysat.logger.info(self.acknowledgements)

    # Define the historic F10.7 starting time
    if self.tag == 'historic':
        self.lasp_stime = lasp_stime

    return


def clean(self):
    """Clean the F10.7 data, empty function as this is not necessary."""

    return


# ----------------------------------------------------------------------------
# Instrument functions


def load(fnames, tag='', inst_id=''):
    """Load F10.7 index files.

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
    if tag in ['historic', 'prelim', 'now']:
        unique_files = list()
        for fname in fnames:
            file_dates.append(dt.datetime.strptime(fname[-10:], '%Y-%m-%d'))
            if fname[0:-11] not in unique_files:
                unique_files.append(fname[0:-11])
        fnames = unique_files

    # Load the CSV data files
    data = pysat.instruments.methods.general.load_csv_data(
        fnames, read_csv_kwargs={"index_col": 0, "parse_dates": True})

    # Rename the GFZ variable name to be consistent with the other data sets
    if tag == 'now':
        data = data.rename(columns={'F{:s}'.format(inst_id): 'f107'})

    # If there is a date range, downselect here
    if len(file_dates) > 0:
        idx, = np.where((data.index >= min(file_dates))
                        & (data.index < max(file_dates) + dt.timedelta(days=1)))
        data = data.iloc[idx, :]

    # Initialize the metadata
    meta = pysat.Meta()
    desc_prefix = '' if inst_id == '' else '{:s} '.format(inst_id.capitalize())
    meta['f107'] = {meta.labels.units: 'SFU',
                    meta.labels.name: 'F10.7 cm solar index',
                    meta.labels.notes: '',
                    meta.labels.desc:
                    '{:s}F10.7 cm radio flux in Solar Flux Units (SFU)'.format(
                        desc_prefix),
                    meta.labels.fill_val: np.nan,
                    meta.labels.min_val: 0,
                    meta.labels.max_val: np.inf}

    if tag == 'historic':
        # LASP updated file format in June, 2022. Minimize impact downstream by
        # continuing use of `f107` as primary data product.
        if 'f107_adjusted' in data.columns:
            # There may be a mix of old and new data formats.
            if 'f107' in data.columns:
                # Only fill NaN in the `f107` and `f107_adjusted` columns
                # for consistency across both data sets
                data.loc[np.isnan(data['f107']), 'f107'] = data.loc[
                    np.isnan(data['f107']), 'f107_adjusted']

                data.loc[np.isnan(data['f107_adjusted']),
                         'f107_adjusted'] = data.loc[
                             np.isnan(data['f107_adjusted']), 'f107']
            else:
                data['f107'] = data['f107_adjusted']

            # Add metadata
            meta['f107_observed'] = meta['f107']
            raw_str = 'Raw F10.7 cm radio flux in Solar Flux Units (SFU)'
            meta['f107_observed'] = {meta.labels.desc: raw_str}

            meta['f107_adjusted'] = meta['f107_observed']
            norm_str = ''.join(['F10.7 cm radio flux in Solar Flux Units (SFU)',
                                ' normalized to 1-AU'])
            meta['f107_adjusted'] = {meta.labels.desc: norm_str}

            meta['f107'] = {
                meta.labels.desc: meta['f107_adjusted', meta.labels.desc]}

    return data, meta


def list_files(tag='', inst_id='', data_path='', format_str=None):
    """List local F10.7 data files.

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

    if tag in ['historic', 'now']:
        # Files are by month, going to add date to monthly filename for
        # each day of the month. The load routine will load a month of
        # data and use the appended date to select out appropriate data.
        if format_str is None:
            if tag == 'historic':
                format_str = 'f107_monthly_{year:04d}-{month:02d}.txt'
            else:
                format_str = 'F{:s}_{{year:04d}}-{{month:02d}}.txt'.format(
                    inst_id)
        out_files = pysat.Files.from_os(data_path=data_path,
                                        format_str=format_str)
        if not out_files.empty:
            out_files.loc[out_files.index[-1] + pds.DateOffset(months=1)
                          - pds.DateOffset(days=1)] = out_files.iloc[-1]
            out_files = out_files.asfreq('D', 'pad')
            out_files = out_files + '_' + out_files.index.strftime(
                '%Y-%m-%d')

    elif tag == 'prelim':
        # Files are by year (and quarter)
        if format_str is None:
            format_str = ''.join(['f107_prelim_{year:04d}_{month:02d}',
                                  '_v{version:01d}.txt'])
        out_files = pysat.Files.from_os(data_path=data_path,
                                        format_str=format_str)

        if not out_files.empty:
            # Set each file's valid length at a 1-day resolution
            orig_files = out_files.sort_index().copy()
            new_files = list()

            for orig in orig_files.items():
                # Version determines each file's valid length
                version = np.int64(orig[1].split("_v")[1][0])
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

    elif tag in ['daily', 'forecast', '45day']:
        out_files = methods.swpc.list_files(name, tag, inst_id, data_path,
                                            format_str=format_str)

    return out_files


def download(date_array, tag, inst_id, data_path, update_files=False,
             mock_download_dir=None):
    """Download F107 index data from the appropriate repository.

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

    Warnings
    --------
    Only able to download current forecast data, not archived forecasts.

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """
    # Download standard F107 data
    if tag == 'historic':
        # Test the date array, updating it if necessary
        if date_array.freq != 'MS':
            date_array = pysat.utils.time.create_date_range(
                dt.datetime(date_array[0].year, date_array[0].month, 1),
                date_array[-1], freq='MS')

        # Download from LASP, by month
        freq = pds.DateOffset(months=1, seconds=-1)
        methods.lisird.download(date_array, data_path, 'f107_monthly_',
                                '%Y-%m', 'noaa_radio_flux', freq, update_files,
                                {'f107_adjusted': -99999.0,
                                 'f107_observed': -99999.0},
                                mock_download_dir=mock_download_dir)

    elif tag == 'prelim':
        # Get the local files, to ensure that the version 1 files are
        # downloaded again if more data has been added
        local_files = list_files(tag, inst_id, data_path)

        # Cut the date from the end of the local files
        for i, lfile in enumerate(local_files):
            local_files[i] = lfile[:-11]

        methods.swpc.old_indices_dsd_download(
            name, date_array, data_path, local_files, today,
            mock_download_dir=mock_download_dir)
    elif tag == 'now':
        # Set the download input options
        gfz_data_name = 'F{:s}'.format(inst_id)
        local_file_prefix = '{:s}_'.format(gfz_data_name)

        # Call the download routine
        methods.gfz.json_downloads(date_array, data_path, local_file_prefix,
                                   "%Y-%m", gfz_data_name,
                                   pds.DateOffset(months=1, seconds=-1),
                                   update_files=update_files,
                                   mock_download_dir=mock_download_dir)

    elif tag == 'daily':
        methods.swpc.daily_dsd_download(name, today, data_path,
                                        mock_download_dir=mock_download_dir)

    elif tag == 'forecast':
        methods.swpc.solar_geomag_predictions_download(
            name, date_array, data_path, mock_download_dir=mock_download_dir)

    elif tag == '45day':
        methods.swpc.recent_ap_f107_download(
            name, date_array, data_path, mock_download_dir=mock_download_dir)

    return
