#!/usr/bin/env python
# -*- coding: utf-8 -*-.
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
#
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
"""Supports Kp index values.

Properties
----------
platform
    'sw'
name
    'kp'
tag
    - '' Deprecated, mixed definitive and nowcast Kp data from GFZ
    - 'def' Definitive Kp data from GFZ
    - 'now' Nowcast Kp data from GFZ
    - 'prediction' Predictions from SWPC for the next 3 days
    - 'forecast' Forecast data from SWPC (next 3 days)
    - 'recent' The last 30 days of Kp data from SWPC
inst_id
    - ''

Note
----
Downloads data from ftp.gfz-potsdam.de or SWPC. These files also contain ap
data (with the GFZ data additionally containing Cp data), and so the additional
data files will be saved to the appropriate data directories to avoid multiple
downloads.

The historic definitive and nowcast Kp files are stored in yearly files, with
the current year being updated remotely on a regular basis.  If you are using
historic data for the current year, we recommend re-downloading it before
performing your data processing.

The forecast data is stored by generation date, where each file contains the
forecast for the next three days. Forecast data downloads are only supported
for the current day. When loading forecast data, the date specified with the
load command is the date the forecast was generated. The data loaded will span
three days. To always ensure you are loading the most recent data, load
the data with tomorrow's date.

Recent data is also stored by the generation date from the SWPC. Each file
contains 30 days of Kp measurements. The load date issued to pysat corresponds
to the generation date.

Examples
--------
::

    kp = pysat.Instrument('sw', 'kp', tag='recent')
    kp.download()
    kp.load(date=kp.tomorrow())


Warnings
--------
The 'forecast', 'prediction', and 'recent' tags load Kp data for a specific
period of time. Loading multiple files, loading multiple days, the data padding
feature, and multi_file_day feature available from the pyast.Instrument object
is not appropriate for these tags data.

"""

import datetime as dt
import numpy as np
import pandas as pds
import warnings

import pysat

from pysatSpaceWeather.instruments import methods

# ----------------------------------------------------------------------------
# Instrument attributes

platform = 'sw'
name = 'kp'
tags = {'': 'Deprecated, mixed definitive and nowcast Kp data from GFZ',
        'def': 'Definitive Kp data from GFZ',
        'now': 'Nowcast Kp data from GFZ',
        'prediction': 'SWPC Predictions for the next three days',
        'forecast': 'SWPC Forecast data next (3 days)',
        'recent': 'SWPC provided Kp for past 30 days'}
inst_ids = {'': list(tags.keys())}

# Generate todays date to support loading forecast data
now = dt.datetime.utcnow()
today = dt.datetime(now.year, now.month, now.day)

# ----------------------------------------------------------------------------
# Instrument test attributes

# Set test dates
_test_dates = {'': {'def': dt.datetime(2009, 1, 1),
                    'now': dt.datetime(2020, 1, 1),
                    'forecast': today + dt.timedelta(days=1),
                    'prediction': today + dt.timedelta(days=1),
                    'recent': today}}

# Other tags assumed to be True
_test_download_ci = {'': {'': False}}

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
    """Load Kp index files.

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

    Warnings
    --------
    tag '' has been deprecated, will be removed in version 0.2.0+

    """

    meta = pysat.Meta()
    if tag == '':
        # This data type has been deprecated due to changes at GFZ
        warnings.warn("".join(["Changes at the GFZ database have led to this",
                               " data type being deprecated. Switch to using",
                               " 'def' for definitive Kp or 'now' for Kp ",
                               "nowcasts from GFZ. Load support will be ",
                               "removed in version 0.2.0+"]),
                      DeprecationWarning, stacklevel=2)

        # Kp data stored monthly, need to return data daily.  The daily date is
        # attached to filename.  Parse off the last date, load month of data,
        # and downselect to the desired day
        data = pds.DataFrame()

        # Set up fixed width format for these files, only selecting the date
        # and daily 3-hour Kp values
        date_slice = slice(0, 6)
        kp_slice = [slice(7, 10), slice(10, 13), slice(13, 16), slice(16, 19),
                    slice(19, 23), slice(23, 26), slice(26, 29), slice(29, 32)]

        # These are monthly files, if a date range is desired, test here.
        # Does not assume an ordered list, but the date range must be continous
        # within a given month.
        unique_fnames = dict()
        for filename in fnames:
            fname = filename[0:-11]
            fdate = dt.datetime.strptime(filename[-10:], '%Y-%m-%d')
            if fname not in unique_fnames.keys():
                unique_fnames[fname] = [fdate]
            else:
                unique_fnames[fname].append(fdate)

        # Load all of the desired filenames
        all_data = []
        for fname in unique_fnames.keys():
            # The daily date is attached to the filename.  Parse off the last
            # date, load month of data, downselect to the desired day
            fdate = min(unique_fnames[fname])

            with open(fname, 'r') as fin:
                temp = fin.readlines()

            if len(temp) == 0:
                pysat.logger.warn('Empty file: {:}'.format(fname))
                continue

            # This file has a different format if it is historic or a file that
            # is being actively updated.  In either case, this line will
            # remove the appropriate number of summmary lines.
            ilast = -1 if temp[-1].find('Mean') > 0 else -4
            temp = np.array(temp[:ilast])

            # Re-format the time data
            temp_index = np.array([dt.datetime.strptime(tline[date_slice],
                                                        '%y%m%d')
                                   for tline in temp])

            idx, = np.where((temp_index >= fdate)
                            & (temp_index < max(unique_fnames[fname])
                               + dt.timedelta(days=1)))

            temp_data = list()
            for tline in temp[idx]:
                temp_data.append(list())
                for col in kp_slice:
                    temp_data[-1].append(tline[col].strip())

            # Select the desired times and add to data list
            all_data.append(pds.DataFrame(temp_data, index=temp_index[idx]))

        # Combine data together
        data = pds.concat(all_data, axis=0, sort=True)

        if len(data.index) > 0:
            # Each column increments UT by three hours. Produce a single data
            # series that has Kp value monotonically increasing in time with
            # appropriate datetime indices
            data_series = pds.Series(dtype='float64')
            for i in np.arange(8):
                tind = data.index + pds.DateOffset(hours=int(3 * i))
                temp = pds.Series(data.iloc[:, i].values, index=tind)
                data_series = pds.concat([data_series, temp])

            data_series = data_series.sort_index()
            data_series.index.name = 'time'

            # Kp comes in non-user friendly values like 2-, 2o, and 2+. Relate
            # these to 1.667, 2.0, 2.333 for processing and user friendliness
            first = np.array([np.float64(str_val[0])
                              for str_val in data_series])
            flag = np.array([str_val[1] for str_val in data_series])

            ind, = np.where(flag == '+')
            first[ind] += 1.0 / 3.0
            ind, = np.where(flag == '-')
            first[ind] -= 1.0 / 3.0

            result = pds.DataFrame(first, columns=['Kp'],
                                   index=data_series.index)
        else:
            result = pds.DataFrame()

        fill_val = np.nan
    elif tag in ['def', 'now']:
        # Load the definitive or nowcast data. The Kp data stored in yearly
        # files, and we need to return data daily.  The daily date is
        # attached to filename.  Parse off the last date, load month of data,
        # and downselect to the desired day
        result = methods.gfz.load_def_now(fnames)
        fill_val = np.nan
    else:
        # Load the prediction, forecast or recent data
        all_data = []
        for fname in fnames:
            result = pds.read_csv(fname, index_col=0, parse_dates=True)
            all_data.append(result)

        result = pds.concat(all_data)
        fill_val = -1

    # Initalize the meta data
    if tag in ['', 'forecast', 'recent', 'prediction']:
        for kk in result.keys():
            methods.kp_ap.initialize_kp_metadata(meta, kk, fill_val)
    else:
        for kk in result.keys():
            if kk.find('Kp') >= 0:
                methods.kp_ap.initialize_kp_metadata(meta, kk, fill_val)
            elif kk.find('Bartels') >= 0:
                methods.kp_ap.initialize_bartel_metadata(meta, kk)

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

    Warnings
    --------
    The '' tag has been deprecated and local file listing support will
    be removed in version 0.2.0+

    """

    if tag == '':
        # This data type has been deprecated due to changes at GFZ
        warnings.warn("".join(["Changes at the GFZ database have led to this",
                               " data type being deprecated. Switch to using",
                               " 'def' for definitive Kp or 'now' for Kp ",
                               "nowcasts from GFZ. Local file listing support ",
                               "will be removed in version 0.2.0+"]),
                      DeprecationWarning, stacklevel=2)

        # Files are by month, going to add date to monthly filename for
        # each day of the month. The load routine will load a month of
        # data and use the appended date to select out appropriate data.
        if format_str is None:
            format_str = 'kp{year:2d}{month:02d}.tab'
        files = pysat.Files.from_os(data_path=data_path, format_str=format_str,
                                    two_digit_year_break=0)
        if not files.empty:
            files.loc[files.index[-1] + pds.DateOffset(months=1)
                      - pds.DateOffset(days=1)] = files.iloc[-1]
            files = files.asfreq('D', 'pad')
            files = files + '_' + files.index.strftime('%Y-%m-%d')
    elif tag in ['def', 'now']:
        files = methods.gfz.kp_ap_cp_list_files(name, tag, inst_id, data_path,
                                                format_str=format_str)
    else:
        files = methods.swpc.list_files(name, tag, inst_id, data_path,
                                        format_str=format_str)

    return files


def download(date_array, tag, inst_id, data_path, mock_download_dir=None):
    """Download the Kp index data from the appropriate repository.

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

    Raises
    ------
    IOError
        If an unknown mock download directory is supplied or there is a problem
        downloading the data.

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    Warnings
    --------
    Only able to download current forecast data, not archived forecasts.

    The '' tag has been deprecated and downloads are no longer supported by
    the source.  Use 'dep' or 'now' instead.

    """

    # Download standard Kp data
    if tag == '':
        # This data type has been deprecated due to changes at GFZ
        warnings.warn("".join(["Changes at the GFZ database have led to this",
                               " data type being deprecated. Switch to using",
                               " 'def' for definitive Kp or 'now' for Kp ",
                               "nowcasts from GFZ. Downloads are no longer ",
                               "supported by GFZ."]),
                      DeprecationWarning, stacklevel=2)
    elif tag in ['def', 'now']:
        methods.gfz.kp_ap_cp_download(platform, name, date_array, tag, inst_id,
                                      data_path, mock_download_dir)
    elif tag == 'forecast':
        methods.swpc.geomag_forecast_download(name, date_array, data_path,
                                              mock_download_dir)
    elif tag == 'recent':
        methods.swpc.kp_ap_recent_download(name, date_array, data_path,
                                           mock_download_dir)
    elif tag == 'prediction':
        methods.swpc.solar_geomag_predictions_download(
            name, date_array, data_path, mock_download_dir)

    return
