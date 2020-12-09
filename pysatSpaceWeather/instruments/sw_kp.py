# -*- coding: utf-8 -*-
"""Supports Kp index values. Downloads data from ftp.gfz-potsdam.de or SWPC.

Properties
----------
platform
    'sw'
name
    'kp'
tag
    - '' Standard Kp data
    - 'forecast' Grab forecast data from SWPC (next 3 days)
    - 'recent' Grab last 30 days of Kp data from SWPC

Note
----
Standard Kp files are stored by the first day of each month. When downloading
use kp.download(start, stop, freq='MS') to only download days that could
possibly have data.  'MS' gives a monthly start frequency.

The forecast data is stored by generation date, where each file contains the
forecast for the next three days. Forecast data downloads are only supported
for the current day. When loading forecast data, the date specified with the
load command is the date the forecast was generated. The data loaded will span
three days. To always ensure you are loading the most recent data, load
the data with tomorrow's date.
::

    kp = pysat.Instrument('sw', 'kp', tag='recent')
    kp.download()
    kp.load(date=kp.tomorrow())

Recent data is also stored by the generation date from the SWPC. Each file
contains 30 days of Kp measurements. The load date issued to pysat corresponds
to the generation date.

The recent and forecast data should not be used with the data padding option
available from pysat.Instrument objects.

Warnings
--------
The 'forecast' Kp data loads three days at a time. The data padding feature
and multi_file_day feature available from the pyast.Instrument object
is not appropriate for Kp 'forecast' data.


This material is based upon work supported by the
National Science Foundation under Grant Number 1259508.

Any opinions, findings, and conclusions or recommendations expressed in this
material are those of the author(s) and do not necessarily reflect the views
of the National Science Foundation.

"""

import datetime as dt
import ftplib
import numpy as np
import os
import pandas as pds
import requests
import sys

import pysat
from pysat.utils.time import parse_date

from pysatSpaceWeather.instruments.methods import kp_ap

logger = pysat.logger

# ----------------------------------------------------------------------------
# Instrument attributes

platform = 'sw'
name = 'kp'
tags = {'': '',
        'forecast': 'SWPC Forecast data next (3 days)',
        'recent': 'SWPC provided Kp for past 30 days'}
inst_ids = {'': ['', 'forecast', 'recent']}

# generate todays date to support loading forecast data
now = dt.datetime.utcnow()
today = dt.datetime(now.year, now.month, now.day)

# ----------------------------------------------------------------------------
# Instrument test attributes

# Set test dates
_test_dates = {'': {'': dt.datetime(2009, 1, 1),
                    'forecast': today + dt.timedelta(days=1),
                    'recent': today}}

# Other tags assumed to be True
_test_download_travis = {'': {'': False}}

# ----------------------------------------------------------------------------
# Instrument methods


def init(self):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.

    """

    self.acknowledgements = kp_ap.acknowledgements(self.name, self.tag)
    self.references = kp_ap.references(self.name, self.tag)
    logger.info(self.acknowledgements)
    return


def clean(self):
    """ Cleaning function for Space Weather indices

    Note
    ----
    Kp doesn't require cleaning
    """
    return


# ----------------------------------------------------------------------------
# Instrument functions


def load(fnames, tag=None, inst_id=None):
    """Load Kp index files

    Parameters
    ----------
    fnames : pandas.Series
        Series of filenames
    tag : str or NoneType
        tag or None (default=None)
    inst_id : str or NoneType
        satellite id or None (default=None)

    Returns
    -------
    data : pandas.DataFrame
        Object containing satellite data
    meta : pysat.Meta
        Object containing metadata such as column names and units

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """

    meta = pysat.Meta()
    if tag == '':
        # Kp data stored monthly, need to return data daily.  The daily date is
        # attached to filename.  Parse off the last date, load month of data,
        # and downselect to the desired day
        data = pds.DataFrame()

        # Set up fixed width format for these files
        colspec = [(0, 2), (2, 4), (4, 6), (7, 10), (10, 13), (13, 16),
                   (16, 19), (19, 23), (23, 26), (26, 29), (29, 32), (32, 50)]
        all_data = []
        for filename in fnames:
            # The daily date is attached to the filename.  Parse off the last
            # date, load month of data, downselect to the desired day
            fname = filename[0:-11]
            date = dt.datetime.strptime(filename[-10:], '%Y-%m-%d')

            temp = pds.read_fwf(fname, colspecs=colspec, skipfooter=4,
                                header=None, parse_dates=[[0, 1, 2]],
                                date_parser=parse_date, index_col='0_1_2')
            idx, = np.where((temp.index >= date)
                            & (temp.index < date + pds.DateOffset(days=1)))
            temp = temp.iloc[idx, :]
            all_data.append(temp)

        # Combine data together
        data = pds.concat(all_data, axis=0, sort=True)

        # Drop last column as it has data that belongs to a different inst
        data = data.iloc[:, 0:-1]

        # Each column increments UT by three hours. Produce a single data
        # series that has Kp value monotonically increasing in time with
        # appropriate datetime indices
        data_series = pds.Series(dtype='float64')
        for i in np.arange(8):
            tind = data.index + pds.DateOffset(hours=int(3 * i))
            temp = pds.Series(data.iloc[:, i].values, index=tind)
            data_series = data_series.append(temp)
        data_series = data_series.sort_index()
        data_series.index.name = 'time'

        # Kp comes in non-user friendly values like 2-, 2o, and 2+. Relate
        # these to 1.667, 2.0, 2.333 for processing and user friendliness
        first = np.array([float(x[0]) for x in data_series])
        flag = np.array([x[1] for x in data_series])

        ind, = np.where(flag == '+')
        first[ind] += 1.0 / 3.0
        ind, = np.where(flag == '-')
        first[ind] -= 1.0 / 3.0

        result = pds.DataFrame(first, columns=['Kp'], index=data_series.index)
        fill_val = np.nan
    elif tag == 'forecast':
        # Load forecast data
        all_data = []
        for fname in fnames:
            result = pds.read_csv(fname, index_col=0, parse_dates=True)
            all_data.append(result)
        result = pds.concat(all_data)
        fill_val = -1
    elif tag == 'recent':
        # Load recent Kp data
        all_data = []
        for fname in fnames:
            result = pds.read_csv(fname, index_col=0, parse_dates=True)
            all_data.append(result)
        result = pds.concat(all_data)
        fill_val = -1

    # Initalize the meta data
    for kk in result.keys():
        kp_ap.initialize_kp_metadata(meta, kk, fill_val)

    return result, meta


def list_files(tag=None, inst_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for chosen satellite data

    Parameters
    -----------
    tag : string or NoneType
        Denotes type of file to load.
        (default=None)
    inst_id : string or NoneType
        Specifies the satellite ID for a constellation.  Not used.
        (default=None)
    data_path : string or NoneType
        Path to data directory.  If None is specified, the value previously
        set in Instrument.files.data_path is used.  (default=None)
    format_str : string or NoneType
        User specified file format.  If None is specified, the default
        formats associated with the supplied tags are used. (default=None)

    Returns
    -------
    pysat.Files.from_os : pysat._files.Files
        A class containing the verified available files

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """

    if data_path is not None:
        if tag == '':
            # Files are by month, going to add date to monthly filename for
            # each day of the month. The load routine will load a month of
            # data and use the appended date to select out appropriate data.
            if format_str is None:
                format_str = 'kp{year:2d}{month:02d}.tab'
            out = pysat.Files.from_os(data_path=data_path,
                                      format_str=format_str,
                                      two_digit_year_break=99)
            if not out.empty:
                out.loc[out.index[-1] + pds.DateOffset(months=1)
                        - pds.DateOffset(days=1)] = out.iloc[-1]
                out = out.asfreq('D', 'pad')
                out = out + '_' + out.index.strftime('%Y-%m-%d')
            return out
        elif tag == 'forecast':
            format_str = 'kp_forecast_{year:04d}-{month:02d}-{day:02d}.txt'
            files = pysat.Files.from_os(data_path=data_path,
                                        format_str=format_str)
            # Pad list of files data to include most recent file under tomorrow
            if not files.empty:
                pds_offset = pds.DateOffset(days=1)
                files.loc[files.index[-1] + pds_offset] = files.values[-1]
                files.loc[files.index[-1] + pds_offset] = files.values[-1]
            return files
        elif tag == 'recent':
            format_str = 'kp_recent_{year:04d}-{month:02d}-{day:02d}.txt'
            files = pysat.Files.from_os(data_path=data_path,
                                        format_str=format_str)

            # Pad list of files data to include most recent file under tomorrow
            if not files.empty:
                pds_offset = pds.DateOffset(days=1)
                files.loc[files.index[-1] + pds_offset] = files.values[-1]
                files.loc[files.index[-1] + pds_offset] = files.values[-1]
            return files

        else:
            raise ValueError(' '.join(('Unrecognized tag name for Space',
                                       'Weather Index Kp')))
    else:
        raise ValueError(' '.join(('A data_path must be passed to the loading',
                                   'routine for Kp')))


def download(date_array, tag, inst_id, data_path, user=None, password=None):
    """Routine to download Kp index data

    Parameters
    -----------
    tag : string or NoneType
        Denotes type of file to load.  Accepted types are '' and 'forecast'.
        (default=None)
    inst_id : string or NoneType
        Specifies the satellite ID for a constellation.  Not used.
        (default=None)
    data_path : string or NoneType
        Path to data directory.  If None is specified, the value previously
        set in Instrument.files.data_path is used.  (default=None)

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    Warnings
    --------
    Only able to download current forecast data, not archived forecasts.

    """

    # Download standard Kp data
    if tag == '':
        ftp = ftplib.FTP('ftp.gfz-potsdam.de')  # connect to host, default port
        ftp.login()  # user anonymous, passwd anonymous@
        ftp.cwd('/pub/home/obs/kp-ap/tab')
        dnames = list()

        for date in date_array:
            fname = 'kp{year:02d}{month:02d}.tab'
            fname = fname.format(year=(date.year - (date.year // 100) * 100),
                                 month=date.month)
            local_fname = fname
            saved_fname = os.path.join(data_path, local_fname)
            if fname not in dnames:
                try:
                    logger.info(' '.join(('Downloading file for',
                                          date.strftime('%b %Y'))))
                    sys.stdout.flush()
                    ftp.retrbinary('RETR ' + fname,
                                   open(saved_fname, 'wb').write)
                    dnames.append(fname)
                except ftplib.error_perm as exception:

                    if str(exception.args[0]).split(" ", 1)[0] != '550':
                        # Leaving a bare raise below so that ftp errors
                        # are properly reported as coming from ftp
                        # and gives the correct line number.
                        # We aren't expecting any 'normal' ftp errors
                        # here, other than a 550 'no file' error, thus
                        # accurately raising FTP issues is the way to go
                        raise
                    else:
                        # File isn't actually there, just let people know
                        # then continue on
                        os.remove(saved_fname)
                        logger.info(' '.join(('File not available for',
                                              date.strftime('%x'))))

        ftp.close()

    elif tag == 'forecast':
        logger.info(' '.join(('This routine can only download the current',
                              'forecast, not archived forecasts')))
        # Download webpage
        furl = 'https://services.swpc.noaa.gov/text/3-day-geomag-forecast.txt'
        r = requests.get(furl)

        # Parse text to get the date the prediction was generated
        date_str = r.text.split(':Issued: ')[-1].split(' UTC')[0]
        date = dt.datetime.strptime(date_str, '%Y %b %d %H%M')

        # Data is the forecast value for the next three days
        raw_data = r.text.split('NOAA Kp index forecast ')[-1]

        # Get date of the forecasts
        date_str = raw_data[0:6] + ' ' + str(date.year)
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
            day1.append(int(raw[0:10]))
            day2.append(int(raw[10:20]))
            day3.append(int(raw[20:]))
        times = pds.date_range(forecast_date, periods=24, freq='3H')
        day = []
        for dd in [day1, day2, day3]:
            day.extend(dd)

        # Put data into nicer DataFrame
        data = pds.DataFrame(day, index=times, columns=['Kp'])

        # Write out as a file
        data_file = 'kp_forecast_{:s}.txt'.format(date.strftime('%Y-%m-%d'))
        data.to_csv(os.path.join(data_path, data_file), header=True)

    elif tag == 'recent':
        logger.info(' '.join(('This routine can only download the current',
                              'webpage, not archived forecasts')))

        # Download webpage
        rurl = ''.join(('https://services.swpc.noaa.gov/text/',
                        'daily-geomagnetic-indices.txt'))
        r = requests.get(rurl)

        # Parse text to get the date the prediction was generated
        date_str = r.text.split(':Issued: ')[-1].split('\n')[0]
        date = dt.datetime.strptime(date_str, '%H%M UT %d %b %Y')

        # Data is the forecast value for the next three days
        raw_data = r.text.split('#  Date ')[-1]

        # Keep only the middle bits that matter
        raw_data = raw_data.split('\n')[1:-1]

        # Hold times from the file
        kp_time = []

        # Holds Kp value for each station
        sub_kps = [[], [], []]

        # Iterate through file lines and parse out the info we want
        for line in raw_data:
            kp_time.append(dt.datetime.strptime(line[0:10], '%Y %m %d'))

            # Pick out Kp values for each of the three columns
            sub_lines = [line[17:33], line[40:56], line[63:]]
            for sub_line, sub_kp in zip(sub_lines, sub_kps):
                for i in np.arange(8):
                    sub_kp.append(int(sub_line[(i * 2):((i + 1) * 2)]))

        # Create times on 3 hour cadence
        times = pds.date_range(kp_time[0], periods=(8 * 30), freq='3H')

        # Put into DataFrame
        data = pds.DataFrame({'mid_lat_Kp': sub_kps[0],
                              'high_lat_Kp': sub_kps[1],
                              'Kp': sub_kps[2]}, index=times)

        # Write out as a file
        data_file = 'kp_recent_{:s}.txt'.format(date.strftime('%Y-%m-%d'))
        data.to_csv(os.path.join(data_path, data_file), header=True)

    return
