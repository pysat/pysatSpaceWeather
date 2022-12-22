# -*- coding: utf-8 -*-
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
    - 'forecast' Grab forecast data from SWPC (next 3 days)
    - 'recent' Grab last 30 days of Kp data from SWPC
inst_id
    ''

Note
----
Downloads data from ftp.gfz-potsdam.de or SWPC.

Standard Kp files are stored by the first day of each month. When downloading
use kp.download(start, stop, freq='MS') to only download days that could
possibly have data.  'MS' gives a monthly start frequency.

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
The 'forecast' and 'recent' tags load Kp data for a specific period of time.
Loading multiple files, loading multiple days, the data padding feature, and
multi_file_day feature available from the pyast.Instrument object is not
appropriate for these tags data.

This material is based upon work supported by the
National Science Foundation under Grant Number 1259508.

Any opinions, findings, and conclusions or recommendations expressed in this
material are those of the author(s) and do not necessarily reflect the views
of the National Science Foundation.

"""

import datetime as dt
import numpy as np
import os
import pandas as pds
import requests
import warnings

import pysat

from pysatSpaceWeather.instruments.methods import general
from pysatSpaceWeather.instruments.methods import kp_ap

# ----------------------------------------------------------------------------
# Instrument attributes

platform = 'sw'
name = 'kp'
tags = {'': 'Deprecated, mixed definitive and nowcast Kp data from GFZ',
        'def': 'Definitive Kp data from GFZ',
        'now': 'Nowcast Kp data from GFZ',
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
                    'recent': today}}

# Other tags assumed to be True
_test_download_ci = {'': {'': False}}

# ----------------------------------------------------------------------------
# Instrument methods

preprocess = general.preprocess


def init(self):
    """Initialize the Instrument object with instrument specific values."""

    self.acknowledgements = kp_ap.acknowledgements(self.name, self.tag)
    self.references = kp_ap.references(self.name, self.tag)
    pysat.logger.info(self.acknowledgements)

    if self.tag in ["def", "now"]:
        # This tag loads more than just Kp data, and the behaviour will be
        # deprecated in v0.1.0
        warnings.warn("".join(["Upcoming structural changes will prevent ",
                               "Instruments from loading multiple data sets ",
                               "in one Instrument. In version 0.1.0+ the Ap ",
                               "and Cp data will be accessable from the ",
                               "`sw_ap` and `sw_cp` Instruments."]),
                      DeprecationWarning, stacklevel=2)

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
        data = pds.DataFrame()

        unique_fnames = dict()
        for filename in fnames:
            fname = filename[0:-11]
            fdate = dt.datetime.strptime(filename[-10:], '%Y-%m-%d')
            if fname not in unique_fnames.keys():
                unique_fnames[fname] = [fdate]
            else:
                unique_fnames[fname].append(fdate)

        # Load the desired filenames
        all_data = []
        for fname in unique_fnames.keys():
            # The daily date is attached to the filename.  Parse off the last
            # date, load the year of data, downselect to the desired day
            fdate = min(unique_fnames[fname])
            temp = pds.read_csv(fname, index_col=0, parse_dates=True)

            if temp.empty:
                pysat.logger.warn('Empty file: {:}'.format(fname))
                continue

            # Select the desired times and add to data list
            all_data.append(pds.DataFrame(temp[fdate:max(unique_fnames[fname])
                                               + dt.timedelta(seconds=86399)]))

        # Combine data together
        if len(all_data) > 0:
            result = pds.concat(all_data, axis=0, sort=True)
        else:
            result = pds.DataFrame()

        fill_val = np.nan
    else:
        # Load the forecast or recent data
        all_data = []
        for fname in fnames:
            result = pds.read_csv(fname, index_col=0, parse_dates=True)
            all_data.append(result)

        result = pds.concat(all_data)
        fill_val = -1

    # Initalize the meta data
    if tag in ['', 'forecast', 'recent']:
        for kk in result.keys():
            kp_ap.initialize_kp_metadata(meta, kk, fill_val)
    else:
        for kk in result.keys():
            if kk.find('Kp') >= 0:
                kp_ap.initialize_kp_metadata(meta, kk, fill_val)
            elif kk.lower().find('ap') >= 0:
                kp_ap.initialize_ap_metadata(meta, kk, fill_val)

        meta['Bartels_solar_rotation_num'] = {
            meta.labels.units: '',
            meta.labels.name: 'Bartels solar rotation number',
            meta.labels.desc: ''.join(['A sequence of 27-day intervals counted',
                                       ' from February 8, 1832']),
            meta.labels.min_val: 1,
            meta.labels.max_val: np.inf,
            meta.labels.fill_val: -1}
        meta['day_within_Bartels_rotation'] = {
            meta.labels.units: 'days',
            meta.labels.name: 'Bartels solar rotation number',
            meta.labels.desc: ''.join(['Number of day within the Bartels solar',
                                       ' rotation']),
            meta.labels.min_val: 1,
            meta.labels.max_val: 27,
            meta.labels.fill_val: -1}
        meta['Cp'] = {
            meta.labels.units: '',
            meta.labels.name: 'Cp index',
            meta.labels.desc: ''.join(['the daily planetary character figure, ',
                                       'a qualitative estimate of the overall ',
                                       'level of geomagnetic activity for ',
                                       'this day determined from the sum of ',
                                       'the eight ap amplitudes']),
            meta.labels.min_val: 0.0,
            meta.labels.max_val: 2.5,
            meta.labels.fill_val: np.nan}
        meta['C9'] = {
            meta.labels.units: '',
            meta.labels.name: 'C9 index',
            meta.labels.desc: ''.join(['the contracted scale for Cp']),
            meta.labels.min_val: 0,
            meta.labels.max_val: 9,
            meta.labels.fill_val: -1}

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
        if format_str is None:
            format_str = ''.join(['Kp_{:s}'.format(tag), '{year:04d}.txt'])

        # Files are stored by year, going to add a date to the yearly
        # filename for each month and day of month.  The load routine will load
        # the year and use the append date to select out approriate data.
        files = pysat.Files.from_os(data_path=data_path, format_str=format_str)
        if not files.empty:
            files.loc[files.index[-1] + pds.DateOffset(years=1)
                      - pds.DateOffset(days=1)] = files.iloc[-1]
            files = files.asfreq('D', 'pad')
            files = files + '_' + files.index.strftime('%Y-%m-%d')
    else:
        if format_str is None:
            format_str = '_'.join(['kp', tag,
                                   '{year:04d}-{month:02d}-{day:02d}.txt'])
        files = pysat.Files.from_os(data_path=data_path, format_str=format_str)

        # Pad list of files data to include most recent file under tomorrow
        if not files.empty:
            pds_offset = pds.DateOffset(days=1)
            files.loc[files.index[-1] + pds_offset] = files.values[-1]
            files.loc[files.index[-1] + pds_offset] = files.values[-1]

    return files


def download(date_array, tag, inst_id, data_path):
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
        # Set the page for the definitive or nowcast Kp
        burl = ''.join(['https://datapub.gfz-potsdam.de/download/10.5880.Kp.',
                        '0001/Kp_', 'nowcast' if tag == 'now' else 'definitive',
                        '/'])
        data_cols = ['Bartels_solar_rotation_num',
                     'day_within_Bartels_rotation', 'Kp', 'daily_Kp_sum', 'ap',
                     'daily_Ap', 'Cp', 'C9']
        hours = np.arange(0, 24, 3)
        kp_translate = {'0': 0.0, '3': 1.0 / 3.0, '7': 2.0 / 3.0}
        dnames = list()

        for dl_date in date_array:
            fname = 'Kp_{:s}{:04d}.wdc'.format(tag, dl_date.year)
            if fname not in dnames:
                pysat.logger.info(' '.join(('Downloading file for',
                                            dl_date.strftime('%Y'))))
                furl = ''.join([burl, fname])
                req = requests.get(furl)

                if req.ok:
                    # Split the file text into lines
                    lines = req.text.split('\n')[:-1]

                    # Remove the header
                    while lines[0].find('#') == 0:
                        lines.pop(0)

                    # Process the data lines
                    ddict = {dkey: list() for dkey in data_cols}
                    times = list()
                    for line in lines:
                        ldate = dt.datetime.strptime(' '.join([
                            "{:02d}".format(int(dd)) for dd in
                            [line[:2], line[2:4], line[4:6]]]), "%y %m %d")
                        bsr_num = np.int64(line[6:10])
                        bsr_day = np.int64(line[10:12])
                        if line[28:30] == '  ':
                            kp_ones = 0.0
                        else:
                            kp_ones = np.float64(line[28:30])
                        sum_kp = kp_ones + kp_translate[line[30]]
                        daily_ap = np.int64(line[55:58])
                        cp = np.float64(line[58:61])
                        c9 = np.int64(line[61])

                        for i, hour in enumerate(hours):
                            # Set the time for this hour and day
                            times.append(ldate + dt.timedelta(hours=int(hour)))

                            # Set the daily values for this hour
                            ddict['Bartels_solar_rotation_num'].append(bsr_num)
                            ddict['day_within_Bartels_rotation'].append(bsr_day)
                            ddict['daily_Kp_sum'].append(sum_kp)
                            ddict['daily_Ap'].append(daily_ap)
                            ddict['Cp'].append(cp)
                            ddict['C9'].append(c9)

                            # Get the hourly-specific values
                            ikp = i * 2
                            kp_ones = line[12 + ikp]
                            if kp_ones == ' ':
                                kp_ones = 0.0
                            ddict['Kp'].append(np.float64(kp_ones)
                                               + kp_translate[line[13 + ikp]])
                            iap = i * 3
                            ddict['ap'].append(np.int64(
                                line[31 + iap:34 + iap]))

                    # Put data into nicer DataFrame
                    data = pds.DataFrame(ddict, index=times, columns=data_cols)

                    # Write out as a CSV file
                    saved_fname = os.path.join(data_path, fname).replace(
                        '.wdc', '.txt')
                    data.to_csv(saved_fname, header=True)

                    # Record the filename so we don't download it twice
                    dnames.append(fname)
                else:
                    pysat.logger.info("".join(["Unable to download data for ",
                                               dl_date.strftime("%d %b %Y"),
                                               ", date may be out of range ",
                                               "for the database."]))

    elif tag == 'forecast':
        pysat.logger.info(' '.join(('This routine can only download the ',
                                    'current forecast, not archived ',
                                    'forecasts')))

        # Download webpage
        furl = 'https://services.swpc.noaa.gov/text/3-day-geomag-forecast.txt'
        req = requests.get(furl)

        # Parse text to get the date the prediction was generated
        date_str = req.text.split(':Issued: ')[-1].split(' UTC')[0]
        dl_date = dt.datetime.strptime(date_str, '%Y %b %d %H%M')

        # Data is the forecast value for the next three days
        raw_data = req.text.split('NOAA Kp index forecast ')[-1]

        # Get date of the forecasts
        date_str = raw_data[0:6] + ' ' + str(dl_date.year)
        forecast_date = dt.datetime.strptime(date_str, '%d %b %Y')

        # Strings we will use to parse the downloaded text
        lines = ['00-03UT', '03-06UT', '06-09UT', '09-12UT', '12-15UT',
                 '15-18UT', '18-21UT', '21-00UT']

        # Storage for daily forecasts.
        # Get values for each day, then combine together
        day1 = []
        day2 = []
        day3 = []
        for line in lines:
            raw = raw_data.split(line)[-1].split('\n')[0]
            cols = raw.split()
            day1.append(np.float64(cols[-3]))
            day2.append(np.float64(cols[-2]))
            day3.append(np.float64(cols[-1]))

        times = pds.date_range(forecast_date, periods=24, freq='3H')
        day = []
        for dd in [day1, day2, day3]:
            day.extend(dd)

        # Put data into nicer DataFrame
        data = pds.DataFrame(day, index=times, columns=['Kp'])

        # Write out as a file
        data_file = 'kp_forecast_{:s}.txt'.format(dl_date.strftime('%Y-%m-%d'))
        data.to_csv(os.path.join(data_path, data_file), header=True)

    elif tag == 'recent':
        pysat.logger.info(' '.join(('This routine can only download the ',
                                    'current webpage, not archived forecasts')))

        # Download webpage
        rurl = ''.join(('https://services.swpc.noaa.gov/text/',
                        'daily-geomagnetic-indices.txt'))
        req = requests.get(rurl)

        # Parse text to get the date the prediction was generated
        date_str = req.text.split(':Issued: ')[-1].split('\n')[0]
        dl_date = dt.datetime.strptime(date_str, '%H%M UT %d %b %Y')

        # Data is the forecast value for the next three days
        raw_data = req.text.split('#  Date ')[-1]

        # Keep only the middle bits that matter
        raw_data = raw_data.split('\n')[1:-1]

        # Hold times from the file
        kp_time = []

        # Holds Kp value for each station
        sub_kps = [[], [], []]

        # Iterate through file lines and parse out the info we want
        for line in raw_data:
            kp_time.append(dt.datetime.strptime(line[0:10], '%Y %m %d'))

            # Pick out Kp values for each of the three columns. The columns
            # used to all have integer values, but now some have floats.
            sub_lines = [line[17:33], line[40:56], line[63:]]
            for i, sub_line in enumerate(sub_lines):
                split_sub = sub_line.split()
                for ihr in np.arange(8):
                    if sub_line.find('.') < 0:
                        # These are integer values
                        sub_kps[i].append(
                            np.int64(sub_line[(ihr * 2):((ihr + 1) * 2)]))
                    else:
                        # These are float values
                        sub_kps[i].append(np.float64(split_sub[ihr]))

        # Create times on 3 hour cadence
        times = pds.date_range(kp_time[0], periods=(8 * 30), freq='3H')

        # Put into DataFrame
        data = pds.DataFrame({'mid_lat_Kp': sub_kps[0],
                              'high_lat_Kp': sub_kps[1],
                              'Kp': sub_kps[2]}, index=times)

        # Write out as a file
        data_file = 'kp_recent_{:s}.txt'.format(dl_date.strftime('%Y-%m-%d'))
        data.to_csv(os.path.join(data_path, data_file), header=True)

    return
