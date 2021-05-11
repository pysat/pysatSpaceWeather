# -*- coding: utf-8 -*-
"""Supports F10.7 index values. Downloads data from LASP and the SWPC.

Properties
----------
platform
    'sw'
name
    'f107'
tag
    - 'historic' LASP F10.7 data (downloads by month, loads by day)
    - 'prelim' Preliminary SWPC daily solar indices
    - 'daily' Daily SWPC solar indices (contains last 30 days)
    - 'forecast' Grab forecast data from SWPC (next 3 days)
    - '45day' 45-Day Forecast data from the Air Force

Example
-------
Download and load all of the historic F10.7 data.  Note that it will not
stop on the current date, but a point in the past when post-processing has
been successfully completed.
::

    f107 = pysat.Instrument('sw', 'f107')
    f107.download(start=f107.lasp_stime, stop=f107.today(), freq='MS')
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


The forecast or prelim data should not be used with the data padding option
available from pysat.Instrument objects. The 'all' tag shouldn't be used either,
no other data available to pad with.

Warnings
--------
The 'forecast' F10.7 data loads three days at a time. The data padding feature
and multi_file_day feature available from the pyast.Instrument object
is not appropriate for 'forecast' data.

"""

import datetime as dt
import ftplib
import json
import numpy as np
import os
import requests
import sys
import warnings

import pandas as pds
import pysat

from pysatSpaceWeather.instruments.methods import f107 as mm_f107
from pysatSpaceWeather.instruments.methods.ace import load_csv_data

logger = pysat.logger

# ----------------------------------------------------------------------------
# Instrument attributes

platform = 'sw'
name = 'f107'
tags = {'historic': 'Daily LASP value of F10.7',
        'prelim': 'Preliminary SWPC daily solar indices',
        'daily': 'Daily SWPC solar indices (contains last 30 days)',
        'forecast': 'SWPC Forecast F107 data next (3 days)',
        '45day': 'Air Force 45-day Forecast'}

# Dict keyed by inst_id that lists supported tags for each inst_id
inst_ids = {'': [tag for tag in tags.keys()]}

# Dict keyed by inst_id that lists supported tags and a good day of test data
# generate todays date to support loading forecast data
now = dt.datetime.utcnow()
today = dt.datetime(now.year, now.month, now.day)
tomorrow = today + pds.DateOffset(days=1)

# The LASP archive start day is also important
lasp_stime = dt.datetime(1947, 2, 14)

# ----------------------------------------------------------------------------
# Instrument test attributes

_test_dates = {'': {'historic': dt.datetime(2009, 1, 1),
                    'prelim': dt.datetime(2009, 1, 1),
                    'daily': tomorrow,
                    'forecast': tomorrow,
                    '45day': tomorrow}}

# Other tags assumed to be True
_test_download_travis = {'': {'prelim': False}}

# ----------------------------------------------------------------------------
# Instrument methods


def init(self):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.

    """

    self.acknowledgements = mm_f107.acknowledgements(self.name, self.tag)
    self.references = mm_f107.references(self.name, self.tag)
    logger.info(self.acknowledgements)

    # Define the historic F10.7 starting time
    if self.tag == 'historic':
        self.lasp_stime = lasp_stime

    return


def clean(self):
    """ Cleaning function for Space Weather indices

    Note
    ----
    F10.7 doesn't require cleaning
    """
    return


# ----------------------------------------------------------------------------
# Instrument functions


def load(fnames, tag=None, inst_id=None):
    """Load F10.7 index files

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
    # Get the desired file dates and file names from the daily indexed list
    file_dates = list()
    if tag == 'historic':
        unique_files = list()
        for fname in fnames:
            file_dates.append(dt.datetime.strptime(fname[-10:], '%Y-%m-%d'))
            if fname[0:-11] not in unique_files:
                unique_files.append(fname[0:-11])
        fnames = unique_files

    # Load the CSV data files
    data = load_csv_data(fnames, read_csv_kwargs={"index_col": 0,
                                                  "parse_dates": True})

    # If there is a date range, downselect here
    if len(file_dates) > 0:
        idx, = np.where((data.index >= min(file_dates))
                        & (data.index < max(file_dates) + dt.timedelta(days=1)))
        data = data.iloc[idx, :]

    # Initialize the metadata
    meta = pysat.Meta()
    meta['f107'] = {meta.labels.units: 'SFU',
                    meta.labels.name: 'F10.7 cm solar index',
                    meta.labels.notes: '',
                    meta.labels.desc:
                    'F10.7 cm radio flux in Solar Flux Units (SFU)',
                    meta.labels.fill_val: np.nan,
                    meta.labels.min_val: 0,
                    meta.labels.max_val: np.inf}

    if tag == '45day':
        meta['ap'] = {meta.labels.units: '',
                      meta.labels.name: 'Daily Ap index',
                      meta.labels.notes: '',
                      meta.labels.desc: 'Daily average of 3-h ap indices',
                      meta.labels.fill_val: np.nan,
                      meta.labels.min_val: 0,
                      meta.labels.max_val: 400}
    elif tag == 'daily' or tag == 'prelim':
        meta['ssn'] = {meta.labels.units: '',
                       meta.labels.name: 'Sunspot Number',
                       meta.labels.notes: '',
                       meta.labels.desc: 'SESC Sunspot Number',
                       meta.labels.fill_val: -999,
                       meta.labels.min_val: 0,
                       meta.labels.max_val: np.inf}
        meta['ss_area'] = {meta.labels.units: '10$^-6$ Solar Hemisphere',
                           meta.labels.name: 'Sunspot Area',
                           meta.labels.notes: '',
                           meta.labels.desc:
                           ''.join(['Sunspot Area in Millionths of the ',
                                    'Visible Hemisphere']),
                           meta.labels.fill_val: -999,
                           meta.labels.min_val: 0,
                           meta.labels.max_val: 1.0e6}
        meta['new_reg'] = {meta.labels.units: '',
                           meta.labels.name: 'New Regions',
                           meta.labels.notes: '',
                           meta.labels.desc: 'New active solar regions',
                           meta.labels.fill_val: -999,
                           meta.labels.min_val: 0,
                           meta.labels.max_val: np.inf}
        meta['smf'] = {meta.labels.units: 'G',
                       meta.labels.name: 'Solar Mean Field',
                       meta.labels.notes: '',
                       meta.labels.desc: 'Standford Solar Mean Field',
                       meta.labels.fill_val: -999,
                       meta.labels.min_val: 0,
                       meta.labels.max_val: np.inf}
        meta['goes_bgd_flux'] = {meta.labels.units: 'W/m^2',
                                 meta.labels.name: 'X-ray Background Flux',
                                 meta.labels.notes: '',
                                 meta.labels.desc:
                                 'GOES15 X-ray Background Flux',
                                 meta.labels.fill_val: '*',
                                 meta.labels.min_val: -np.inf,
                                 meta.labels.max_val: np.inf}
        meta['c_flare'] = {meta.labels.units: '',
                           meta.labels.name: 'C X-Ray Flares',
                           meta.labels.notes: '',
                           meta.labels.desc: 'C-class X-Ray Flares',
                           meta.labels.fill_val: -1,
                           meta.labels.min_val: 0,
                           meta.labels.max_val: 9}
        meta['m_flare'] = {meta.labels.units: '',
                           meta.labels.name: 'M X-Ray Flares',
                           meta.labels.notes: '',
                           meta.labels.desc: 'M-class X-Ray Flares',
                           meta.labels.fill_val: -1,
                           meta.labels.min_val: 0,
                           meta.labels.max_val: 9}
        meta['x_flare'] = {meta.labels.units: '',
                           meta.labels.name: 'X X-Ray Flares',
                           meta.labels.notes: '',
                           meta.labels.desc: 'X-class X-Ray Flares',
                           meta.labels.fill_val: -1,
                           meta.labels.min_val: 0,
                           meta.labels.max_val: 9}
        meta['o1_flare'] = {meta.labels.units: '',
                            meta.labels.name: '1 Optical Flares',
                            meta.labels.notes: '',
                            meta.labels.desc: '1-class Optical Flares',
                            meta.labels.fill_val: -1,
                            meta.labels.min_val: 0,
                            meta.labels.max_val: 9}
        meta['o2_flare'] = {meta.labels.units: '',
                            meta.labels.name: '2 Optical Flares',
                            meta.labels.notes: '',
                            meta.labels.desc: '2-class Optical Flares',
                            meta.labels.fill_val: -1,
                            meta.labels.min_val: 0,
                            meta.labels.max_val: 9}
        meta['o3_flare'] = {meta.labels.units: '',
                            meta.labels.name: '3 Optical Flares',
                            meta.labels.notes: '',
                            meta.labels.desc: '3-class Optical Flares',
                            meta.labels.fill_val: -1,
                            meta.labels.min_val: 0,
                            meta.labels.max_val: 9}

    return data, meta


def list_files(tag=None, inst_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for F10.7 data

    Parameters
    ----------
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
    out_files : pysat._files.Files
        A class containing the verified available files

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """

    if data_path is not None:
        if tag == 'historic':
            # Files are by month, going to add date to monthly filename for
            # each day of the month. The load routine will load a month of
            # data and use the appended date to select out appropriate data.
            if format_str is None:
                format_str = 'f107_monthly_{year:04d}-{month:02d}.txt'
            out_files = pysat.Files.from_os(data_path=data_path,
                                            format_str=format_str)
            if not out_files.empty:
                out_files.loc[out_files.index[-1] + pds.DateOffset(months=1)
                              - pds.DateOffset(days=1)] = out_files.iloc[-1]
                out_files = out_files.asfreq('D', 'pad')
                out_files = out_files + '_' + out_files.index.strftime(
                    '%Y-%m-%d')

        elif tag == 'prelim':
            # Files are by year (and quarter). The load routine will load a
            # year of data
            if format_str is None:
                format_str = \
                    'f107_prelim_{year:04d}_{month:02d}_v{version:01d}.txt'
            out_files = pysat.Files.from_os(data_path=data_path,
                                            format_str=format_str)

            if not out_files.empty:
                # Set each file's valid length at a 1-day resolution
                orig_files = out_files.sort_index().copy()
                new_files = list()

                for orig in orig_files.iteritems():
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

        elif tag in ['daily', 'forecast', '45day']:
            format_str = ''.join(['f107_', tag,
                                  '_{year:04d}-{month:02d}-{day:02d}.txt'])
            out_files = pysat.Files.from_os(data_path=data_path,
                                            format_str=format_str)

            # Pad list of files data to include most recent file under tomorrow
            if not out_files.empty:
                pds_off = pds.DateOffset(days=1)
                out_files.loc[out_files.index[-1]
                              + pds_off] = out_files.values[-1]
                out_files.loc[out_files.index[-1]
                              + pds_off] = out_files.values[-1]

        else:
            raise ValueError(' '.join(('Unrecognized tag name for Space',
                                       'Weather Index F107:', tag)))
    else:
        raise ValueError(' '.join(('A data_path must be passed to the loading',
                                   'routine for F107')))

    return out_files


def download(date_array, tag, inst_id, data_path, update_files=False):
    """Routine to download F107 index data

    Parameters
    -----------
    date_array : list-like
        Sequence of dates to download date for.
    tag : string or NoneType
        Denotes type of file to load.
    inst_id : string or NoneType
        Specifies the satellite ID for a constellation.
    data_path : string or NoneType
        Path to data directory.
    update_files : bool
        Re-download data for files that already exist if True (default=False)

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    Warnings
    --------
    Only able to download current forecast data, not archived forecasts.

    """

    # download standard F107 data
    if tag == 'historic':
        # Test the date array, updating it if necessary
        if date_array.freq != 'MS':
            warnings.warn(''.join(['Historic F10.7 downloads should be invoked',
                                   " with the `freq='MS'` option."]))
            date_array = pysat.utils.time.create_date_range(
                dt.datetime(date_array[0].year, date_array[0].month, 1),
                date_array[-1], freq='MS')

        # Download from LASP, by month
        for dl_date in date_array:
            # Create the name to which the local file will be saved
            str_date = dl_date.strftime('%Y-%m')
            data_file = os.path.join(data_path,
                                     'f107_monthly_{:s}.txt'.format(str_date))

            if update_files or not os.path.isfile(data_file):
                # Set the download webpage
                dstr = ''.join(['http://lasp.colorado.edu/lisird/latis/dap/',
                                'noaa_radio_flux.json?time%3E=',
                                dl_date.strftime('%Y-%m-%d'),
                                'T00:00:00.000Z&time%3C=',
                                (dl_date + pds.DateOffset(months=1)
                                 - pds.DateOffset(days=1)).strftime('%Y-%m-%d'),
                                'T00:00:00.000Z'])

                # The data is returned as a JSON file
                req = requests.get(dstr)

                # Process the JSON file
                raw_dict = json.loads(req.text)['noaa_radio_flux']
                data = pds.DataFrame.from_dict(raw_dict['samples'])
                if data.empty:
                    warnings.warn("no data for {:}".format(dl_date),
                                  UserWarning)
                else:
                    # The file format changed over time
                    try:
                        # This is the new data format
                        times = [dt.datetime.strptime(time, '%Y%m%d')
                                 for time in data.pop('time')]
                    except ValueError:
                        # Accepts old file formats
                        times = [dt.datetime.strptime(time, '%Y %m %d')
                                 for time in data.pop('time')]
                    data.index = times

                    # Replace fill value with NaNs
                    idx, = np.where(data['f107'] == -99999.0)
                    data.iloc[idx, :] = np.nan

                    # Create a local CSV file
                    data.to_csv(data_file, header=True)
    elif tag == 'prelim':
        ftp = ftplib.FTP('ftp.swpc.noaa.gov')  # connect to host, default port
        ftp.login()  # user anonymous, passwd anonymous@
        ftp.cwd('/pub/indices/old_indices')

        bad_fname = list()

        # Get the local files, to ensure that the version 1 files are
        # downloaded again if more data has been added
        local_files = list_files(tag, inst_id, data_path)

        # To avoid downloading multiple files, cycle dates based on file length
        dl_date = date_array[0]
        while dl_date <= date_array[-1]:
            # The file name changes, depending on how recent the requested
            # data is
            qnum = (dl_date.month - 1) // 3 + 1  # Integer floor division
            qmonth = (qnum - 1) * 3 + 1
            quar = 'Q{:d}_'.format(qnum)
            fnames = ['{:04d}{:s}DSD.txt'.format(dl_date.year, ss)
                      for ss in ['_', quar]]
            versions = ["01_v2", "{:02d}_v1".format(qmonth)]
            vend = [dt.datetime(dl_date.year, 12, 31),
                    dt.datetime(dl_date.year, qmonth, 1)
                    + pds.DateOffset(months=3) - pds.DateOffset(days=1)]
            downloaded = False
            rewritten = False

            # Attempt the download(s)
            for iname, fname in enumerate(fnames):
                # Test to see if we already tried this filename
                if fname in bad_fname:
                    continue

                local_fname = fname
                saved_fname = os.path.join(data_path, local_fname)
                ofile = '_'.join(['f107', 'prelim',
                                  '{:04d}'.format(dl_date.year),
                                  '{:s}.txt'.format(versions[iname])])
                outfile = os.path.join(data_path, ofile)

                if os.path.isfile(outfile):
                    downloaded = True

                    # Check the date to see if this should be rewritten
                    checkfile = os.path.split(outfile)[-1]
                    has_file = local_files == checkfile
                    if np.any(has_file):
                        if has_file[has_file].index[-1] < vend[iname]:
                            # This file will be updated again, but only attempt
                            # to do so if enough time has passed from the
                            # last time it was downloaded
                            yesterday = today - pds.DateOffset(days=1)
                            if has_file[has_file].index[-1] < yesterday:
                                rewritten = True
                else:
                    # The file does not exist, if it can be downloaded, it
                    # should be 'rewritten'
                    rewritten = True

                # Attempt to download if the file does not exist or if the
                # file has been updated
                if rewritten or not downloaded:
                    try:
                        sys.stdout.flush()
                        ftp.retrbinary('RETR ' + fname,
                                       open(saved_fname, 'wb').write)
                        downloaded = True
                        logger.info(' '.join(('Downloaded file for ',
                                              dl_date.strftime('%x'))))

                    except ftplib.error_perm as exception:
                        # Could not fetch, so cannot rewrite
                        rewritten = False

                        # Test for an error
                        if str(exception.args[0]).split(" ", 1)[0] != '550':
                            raise RuntimeError(exception)
                        else:
                            # file isn't actually there, try the next name
                            os.remove(saved_fname)

                            # Save this so we don't try again
                            # Because there are two possible filenames for
                            # each time, it's ok if one isn't there.  We just
                            # don't want to keep looking for it.
                            bad_fname.append(fname)

                # If the first file worked, don't try again
                if downloaded:
                    break

            if not downloaded:
                logger.info(' '.join(('File not available for',
                                      dl_date.strftime('%x'))))
            elif rewritten:
                with open(saved_fname, 'r') as fprelim:
                    lines = fprelim.read()

                rewrite_daily_file(dl_date.year, outfile, lines)
                os.remove(saved_fname)

            # Cycle to the next date
            dl_date = vend[iname] + pds.DateOffset(days=1)

        # Close connection after downloading all dates
        ftp.close()

    elif tag == 'daily':
        logger.info('This routine can only download the latest 30 day file')

        # Set the download webpage
        furl = 'https://services.swpc.noaa.gov/text/daily-solar-indices.txt'
        req = requests.get(furl)

        # Save the output
        data_file = 'f107_daily_{:s}.txt'.format(today.strftime('%Y-%m-%d'))
        outfile = os.path.join(data_path, data_file)
        rewrite_daily_file(today.year, outfile, req.text)

    elif tag == 'forecast':
        logger.info(' '.join(('This routine can only download the current',
                              'forecast, not archived forecasts')))
        # Set the download webpage
        furl = ''.join(('https://services.swpc.noaa.gov/text/',
                        '3-day-solar-geomag-predictions.txt'))
        req = requests.get(furl)

        # Parse text to get the date the prediction was generated
        date_str = req.text.split(':Issued: ')[-1].split(' UTC')[0]
        dl_date = dt.datetime.strptime(date_str, '%Y %b %d %H%M')

        # Get starting date of the forecasts
        raw_data = req.text.split(':Prediction_dates:')[-1]
        forecast_date = dt.datetime.strptime(raw_data[3:14], '%Y %b %d')

        # Set the times for output data
        times = pds.date_range(forecast_date, periods=3, freq='1D')

        # String data is the forecast value for the next three days
        raw_data = req.text.split('10cm_flux:')[-1]
        raw_data = raw_data.split('\n')[1]
        val1 = int(raw_data[24:27])
        val2 = int(raw_data[38:41])
        val3 = int(raw_data[52:])

        # Put data into nicer DataFrame
        data = pds.DataFrame([val1, val2, val3], index=times, columns=['f107'])

        # Write out as a file
        data_file = 'f107_forecast_{:s}.txt'.format(
            dl_date.strftime('%Y-%m-%d'))
        data.to_csv(os.path.join(data_path, data_file), header=True)

    elif tag == '45day':
        logger.info(' '.join(('This routine can only download the current',
                              'forecast, not archived forecasts')))

        # Set the download webpage
        furl = 'https://services.swpc.noaa.gov/text/45-day-ap-forecast.txt'
        req = requests.get(furl)

        # Parse text to get the date the prediction was generated
        date_str = req.text.split(':Issued: ')[-1].split(' UTC')[0]
        dl_date = dt.datetime.strptime(date_str, '%Y %b %d %H%M')

        # Get to the forecast data
        raw_data = req.text.split('45-DAY AP FORECAST')[-1]

        # Grab AP part
        raw_ap = raw_data.split('45-DAY F10.7 CM FLUX FORECAST')[0]
        raw_ap = raw_ap.split('\n')[1:-1]

        # Get the F107
        raw_f107 = raw_data.split('45-DAY F10.7 CM FLUX FORECAST')[-1]
        raw_f107 = raw_f107.split('\n')[1:-4]

        # Parse the AP data
        ap_times, ap = parse_45day_block(raw_ap)

        # Parse the F10.7 data
        f107_times, f107 = parse_45day_block(raw_f107)

        # Collect into DataFrame
        data = pds.DataFrame(f107, index=f107_times, columns=['f107'])
        data['ap'] = ap

        # Write out as a file
        data_file = 'f107_45day_{:s}.txt'.format(dl_date.strftime('%Y-%m-%d'))
        data.to_csv(os.path.join(data_path, data_file), header=True)

    return


# ----------------------------------------------------------------------------
# Local functions


def parse_45day_block(block_lines):
    """ Parse the data blocks used in the 45-day Ap and F10.7 Flux Forecast
    file

    Parameters
    ----------
    block_lines : list
        List of lines containing data in this data block

    Returns
    -------
    dates : list
        List of dates for each date/data pair in this block
    values : list
        List of values for each date/data pair in this block

    """

    # Initialize the output
    dates = list()
    values = list()

    # Cycle through each line in this block
    for line in block_lines:
        # Split the line on whitespace
        split_line = line.split()

        # Format the dates
        dates.extend([dt.datetime.strptime(tt, "%d%b%y")
                      for tt in split_line[::2]])

        # Format the data values
        values.extend([int(vv) for vv in split_line[1::2]])

    return dates, values


def rewrite_daily_file(year, outfile, lines):
    """ Rewrite the SWPC Daily Solar Data files

    Parameters
    ----------
    year : int
        Year of data file (format changes based on date)
    outfile : str
        Output filename
    lines : str
        String containing all output data (result of 'read')

    """

    # get to the solar index data
    if year > 2000:
        raw_data = lines.split('#---------------------------------')[-1]
        raw_data = raw_data.split('\n')[1:-1]
        optical = True
    else:
        raw_data = lines.split('# ')[-1]
        raw_data = raw_data.split('\n')
        optical = False if raw_data[0].find('Not Available') or year == 1994 \
            else True
        istart = 7 if year < 2000 else 1
        raw_data = raw_data[istart:-1]

    # parse the data
    solar_times, data_dict = parse_daily_solar_data(raw_data, year, optical)

    # collect into DataFrame
    data = pds.DataFrame(data_dict, index=solar_times,
                         columns=data_dict.keys())

    # write out as a file
    data.to_csv(outfile, header=True)

    return


def parse_daily_solar_data(data_lines, year, optical):
    """ Parse the data in the SWPC daily solar index file

    Parameters
    ----------
    data_lines : list
        List of lines containing data
    year : list
        Year of file
    optical : boolean
        Flag denoting whether or not optical data is available

    Returns
    -------
    dates : list
        List of dates for each date/data pair in this block
    values : dict
        Dict of lists of values, where each key is the value name

    """

    # Initialize the output
    dates = list()
    val_keys = ['f107', 'ssn', 'ss_area', 'new_reg', 'smf', 'goes_bgd_flux',
                'c_flare', 'm_flare', 'x_flare', 'o1_flare', 'o2_flare',
                'o3_flare']
    optical_keys = ['o1_flare', 'o2_flare', 'o3_flare']
    xray_keys = ['c_flare', 'm_flare', 'x_flare']
    values = {kk: list() for kk in val_keys}

    # Cycle through each line in this file
    for line in data_lines:
        # Split the line on whitespace
        split_line = line.split()

        # Format the date
        dfmt = "%Y %m %d" if year > 1996 else "%d %b %y"
        dates.append(dt.datetime.strptime(" ".join(split_line[0:3]), dfmt))

        # Format the data values
        j = 0
        for i, kk in enumerate(val_keys):
            if year == 1994 and kk == 'new_reg':
                # New regions only in files after 1994
                val = -999
            elif((year == 1994 and kk in xray_keys)
                 or (not optical and kk in optical_keys)):
                # X-ray flares in files after 1994, optical flares come later
                val = -1
            else:
                val = split_line[j + 3]
                j += 1

            if kk != 'goes_bgd_flux':
                if val == "*":
                    val = -999 if i < 5 else -1
                else:
                    val = int(val)
            values[kk].append(val)

    return dates, values


def calc_f107a(f107_inst, f107_name='f107', f107a_name='f107a', min_pnts=41):
    """ Calculate the 81 day mean F10.7

    Parameters
    ----------
    f107_inst : pysat.Instrument
        pysat Instrument holding the F10.7 data
    f107_name : str
        Data column name for the F10.7 data (default='f107')
    f107a_name : str
        Data column name for the F10.7a data (default='f107a')
    min_pnts : int
        Minimum number of points required to calculate an average (default=41)

    Returns
    -------
    Void : Updates f107_inst with F10.7a data

    Notes
    -----
    Will not pad data on its own

    """

    # Test to see that the input data is present
    if f107_name not in f107_inst.data.columns:
        raise ValueError("unknown input data column: " + f107_name)

    # Test to see that the output data does not already exist
    if f107a_name in f107_inst.data.columns:
        raise ValueError("output data column already exists: " + f107a_name)

    if f107_name in f107_inst.meta:
        fill_val = f107_inst.meta[f107_name][f107_inst.meta.labels.fill_val]
    else:
        fill_val = np.nan

    # Calculate the rolling mean.  Since these values are centered but rolling
    # function doesn't allow temporal windows to be calculated this way, create
    # a hack for this.
    #
    # Ensure the data are evenly sampled at a daily frequency, since this is
    # how often F10.7 is calculated.
    f107_fill = f107_inst.data.resample('1D').fillna(method=None)

    # Replace the time index with an ordinal
    time_ind = f107_fill.index
    f107_fill['ord'] = pds.Series([tt.toordinal() for tt in time_ind],
                                  index=time_ind)
    f107_fill.set_index('ord', inplace=True)

    # Calculate the mean
    f107_fill[f107a_name] = f107_fill[f107_name].rolling(window=81,
                                                         min_periods=min_pnts,
                                                         center=True).mean()

    # Replace the ordinal index with the time
    f107_fill['time'] = pds.Series(time_ind, index=f107_fill.index)
    f107_fill.set_index('time', inplace=True)

    # Resample to the original frequency, if it is not equal to 1 day
    freq = pysat.utils.time.calc_freq(f107_inst.index)
    if freq != "86400S":
        # Resample to the desired frequency
        f107_fill = f107_fill.resample(freq).pad()

        # Save the output in a list
        f107a = list(f107_fill[f107a_name])

        # Fill any dates that fall
        time_ind = pds.date_range(f107_fill.index[0], f107_inst.index[-1],
                                  freq=freq)
        for itime in time_ind[f107_fill.index.shape[0]:]:
            if (itime - f107_fill.index[-1]).total_seconds() < 86400.0:
                f107a.append(f107a[-1])
            else:
                f107a.append(fill_val)

        # Redefine the Series
        f107_fill = pds.DataFrame({f107a_name: f107a}, index=time_ind)

    # There may be missing days in the output data, remove these
    if f107_inst.index.shape < f107_fill.index.shape:
        f107_fill = f107_fill.loc[f107_inst.index]

    # Save the data
    f107_inst[f107a_name] = f107_fill[f107a_name]

    # Update the metadata
    meta_dict = {f107_inst.meta.labels.units: 'SFU',
                 f107_inst.meta.labels.name: 'F10.7a',
                 f107_inst.meta.labels.desc: "81-day centered average of F10.7",
                 f107_inst.meta.labels.min_val: 0.0,
                 f107_inst.meta.labels.max_val: np.nan,
                 f107_inst.meta.labels.fill_val: fill_val,
                 f107_inst.meta.labels.notes:
                 ' '.join(('Calculated using data between',
                           '{:} and {:}'.format(f107_inst.index[0],
                                                f107_inst.index[-1])))}

    f107_inst.meta[f107a_name] = meta_dict

    return
