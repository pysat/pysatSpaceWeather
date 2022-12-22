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
import ftplib
import numpy as np
import os
import pandas as pds
import pysat
import requests
import sys
import warnings

from pysatSpaceWeather.instruments.methods import f107 as mm_f107
from pysatSpaceWeather.instruments.methods import general
from pysatSpaceWeather.instruments.methods import lisird

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
_test_download_ci = {'': {'prelim': False}}

# ----------------------------------------------------------------------------
# Instrument methods

preprocess = general.preprocess


def init(self):
    """Initialize the Instrument object with instrument specific values."""

    # Set the required Instrument attributes
    self.acknowledgements = mm_f107.acknowledgements(self.tag)
    self.references = mm_f107.references(self.tag)
    logger.info(self.acknowledgements)

    # Define the historic F10.7 starting time
    if self.tag == 'historic':
        self.lasp_stime = lasp_stime

    # Raise Deprecation warnings
    if self.tag in ['daily', 'prelim']:
        # This tag loads more than just F10.7 data, and the behaviour will be
        # deprecated in v0.1.0
        warnings.warn("".join(["Upcoming structural changes will prevent ",
                               "Instruments from loading multiple data sets in",
                               " one Instrument. In version 0.1.0+ the SSN, ",
                               "solar flare, and solar mean field data will be",
                               " accessable from the `sw_ssn`, `sw_flare`, ",
                               "and `sw_sbfield` Instruments."]),
                      DeprecationWarning, stacklevel=2)
    elif self.tag == '45day':
        # This tag loads more than just F10.7 data, and the behaviour will be
        # deprecated in v0.1.0
        warnings.warn("".join(["Upcoming structural changes will prevent ",
                               "Instruments from loading multiple data sets in",
                               " one Instrument. In version 0.1.0+ the Ap will",
                               " be accessable from the `sw_ap` Instrument."]),
                      DeprecationWarning, stacklevel=2)

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
    if tag in ['historic', 'prelim']:
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
    elif tag == 'historic':
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

    elif tag == 'daily' or tag == 'prelim':
        # Update the allowed types for the fill value
        meta.labels.label_type['fill_val'] = (float, int, np.float64,
                                              np.int64, str)

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
        format_str = ''.join(['f107_', tag,
                              '_{year:04d}-{month:02d}-{day:02d}.txt'])
        out_files = pysat.Files.from_os(data_path=data_path,
                                        format_str=format_str)

        # Pad list of files data to include most recent file under tomorrow
        if not out_files.empty:
            pds_off = pds.DateOffset(days=1)
            out_files.loc[out_files.index[-1] + pds_off] = out_files.values[-1]
            out_files.loc[out_files.index[-1] + pds_off] = out_files.values[-1]

    return out_files


def download(date_array, tag, inst_id, data_path, update_files=False):
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

    Raises
    ------
    IOError
        If a problem is encountered connecting to the gateway or retrieving
        data from the repository.

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
        lisird.download(date_array, data_path, 'f107_monthly_', '%Y-%m',
                        'noaa_radio_flux', freq, update_files,
                        {'f107_adjusted': -99999.0, 'f107_observed': -99999.0})

    elif tag == 'prelim':
        ftp = ftplib.FTP('ftp.swpc.noaa.gov')  # Connect to host, default port
        ftp.login()  # User anonymous, passwd anonymous
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
                            raise IOError(exception)
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

                mm_f107.rewrite_daily_file(dl_date.year, outfile, lines)
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
        mm_f107.rewrite_daily_file(today.year, outfile, req.text)

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
        val1 = np.int64(raw_data[24:27])
        val2 = np.int64(raw_data[38:41])
        val3 = np.int64(raw_data[52:])

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
        ap_times, ap = mm_f107.parse_45day_block(raw_ap)

        # Parse the F10.7 data
        f107_times, f107 = mm_f107.parse_45day_block(raw_f107)

        # Collect into DataFrame
        data = pds.DataFrame(f107, index=f107_times, columns=['f107'])
        data['ap'] = ap

        # Write out as a file
        data_file = 'f107_45day_{:s}.txt'.format(dl_date.strftime('%Y-%m-%d'))
        data.to_csv(os.path.join(data_path, data_file), header=True)

    return
