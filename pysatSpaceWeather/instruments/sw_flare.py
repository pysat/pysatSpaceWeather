# -*- coding: utf-8 -*-
"""Supports F10.7 index values. Downloads data from LASP and the SWPC.

Properties
----------
platform
    'sw'
name
    'flare'
tag
    - 'prelim' Preliminary SWPC daily solar indices
    - 'daily' Daily SWPC solar indices (contains last 30 days)
    - 'prediction' Predictions from SWPC for the next 3 days

Examples
--------
Download and load the most recent flare predictions. To always ensure you are
loading the most recent data, load the data with tomorrow's date.
::

    flare = pysat.Instrument('sw', 'flare', tag='prediction')
    flare.download(start=flare.tomorrow())
    flare.load(date=flare.tomorrow())


Note
----
The forecast data is stored by generation date, where each file contains the
forecast for the next three days. Forecast data downloads are only supported
for the current day. When loading forecast data, the date specified with the
load command is the date the forecast was generated. The data loaded will span
three days. To always ensure you are loading the most recent data, load
the data with tomorrow's date.


Warnings
--------
The 'prediction' F10.7 data loads three days at a time. Loading multiple files,
loading multiple days, the data padding feature, and multi_file_day feature
available from the pyast.Instrument object is not appropriate for 'prediction'
data.

"""

import datetime as dt
import ftplib
import numpy as np
import os
import pandas as pds
import pysat
import requests
import sys

from pysatSpaceWeather.instruments import methods

logger = pysat.logger

# ----------------------------------------------------------------------------
# Instrument attributes

platform = 'sw'
name = 'flare'
tags = {'prelim': 'Preliminary SWPC daily solar indices',
        'daily': 'Daily SWPC solar indices (contains last 30 days)',
        'prediction': 'Predictions from SWPC for the next 3 days'}

# Dict keyed by inst_id that lists supported tags for each inst_id
inst_ids = {'': [tag for tag in tags.keys()]}

# Dict keyed by inst_id that lists supported tags and a good day of test data
# generate todays date to support loading forecast data
now = dt.datetime.utcnow()
today = dt.datetime(now.year, now.month, now.day)
tomorrow = today + dt.datetime(days=1)

# ----------------------------------------------------------------------------
# Instrument test attributes

_test_dates = {'': {'prelim': dt.datetime(2009, 1, 1),
                    'daily': tomorrow,
                    'prediction': tomorrow}}

# Other tags assumed to be True
_test_download_ci = {'': {'prelim': False}}

# ----------------------------------------------------------------------------
# Instrument methods

preprocess = methods.general.preprocess


def init(self):
    """Initialize the Instrument object with instrument specific values."""

    # Set the required Instrument attributes
    self.acknowledgements = methods.swpc.ackn
    self.references = "".join(["Check SWPC for appropriate references: ",
                               "https://www.swpc.noaa.gov/phenomena"])
    logger.info(self.acknowledgements)

    return


def clean(self):
    """Clean the F10.7 data, empty function as this is not necessary."""

    return


# ----------------------------------------------------------------------------
# Instrument functions


def load(fnames, tag='', inst_id=''):
    """Load the solar flare files.

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
    if tag in ['prelim']:
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
    if tag == 'daily' or tag == 'prelim':
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
    elif tag == 'prediction':
        for dkey in data.columns:
            if dkey.find('Region') < 0:
                meta[dkey] = {meta.labels.units: '',
                              meta.labels.name: dkey,
                              meta.labels.notes: '',
                              meta.labels.desc: ''.join([dkey.replace('_', ' '),
                                                         ' Probabilities']),
                              meta.labels.fill_val: -1,
                              meta.labels.min_val: 0,
                              meta.labels.max_val: 100}
            else:
                meta[dkey] = {meta.labels.units: '',
                              meta.labels.name: dkey,
                              meta.labels.notes: '',
                              meta.labels.desc: 'SWPC Solar Region Number',
                              meta.labels.fill_val: -1,
                              meta.labels.min_val: 1,
                              meta.labels.max_val: 9999}

    return data, meta


def list_files(tag='', inst_id='', data_path='', format_str=None):
    """List local solar flare data files.

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
            format_str = ''.join(['flare_prelim_{year:04d}_{month:02d}',
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

    else:
        methods.swpc.list_files(name, tag, inst_id, data_path,
                                format_str=format_str)

    return out_files


def download(date_array, tag, inst_id, data_path, update_files=False):
    """Download solar flare data from the appropriate repository.

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
    if tag == 'prelim':
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

                methods.f107.rewrite_daily_file(dl_date.year, outfile, lines)
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
        methods.f107.rewrite_daily_file(today.year, outfile, req.text)

    elif tag == 'prediction':
        methods.swpc.solar_geomag_predictions_download(name, date_array,
                                                       data_path)

    return
