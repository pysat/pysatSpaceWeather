# -*- coding: utf-8 -*-
"""Supports Dst values. Downloads data from NGDC.

Properties
----------
platform
    'sw'
name
    'dst'
tag
    'noaa' - Historic Dst data coalated by and maintained by NOAA/NCEI
    'lasp' - Predicted Dst from real-time ACE or DSCOVR provided by LASP
inst_id
    ''

Note
----
Will only work until 2057.

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

import pysat

from pysatSpaceWeather.instruments.methods import dst as mm_dst

# ----------------------------------------------------------------------------
# Instrument attributes

platform = 'sw'
name = 'dst'
tags = {'noaa': 'Historic Dst data coalated by and maintained by NOAA/NCEI',
        'lasp': 'Predicted Dst from real-time ACE or DSCOVR provided by LASP'}
inst_ids = {'': [tag for tag in tags.keys()]}

# Generate today's date to support loading predicted data sets
today = pysat.utils.time.today()
tomorrow = today + dt.timedelta(days=1)

# ----------------------------------------------------------------------------
# Instrument test attributes

_test_dates = {'': {'noaa': dt.datetime(2007, 1, 1), 'lasp': today}}

# Other tags assumed to be True
_test_download_ci = {'': {'noaa': False}}

# ----------------------------------------------------------------------------
# Instrument methods


def init(self):
    """Initialize the Instrument object with instrument specific values."""

    self.acknowledgements = mm_dst.acknowledgements(self.tag)
    self.references = mm_dst.references(self.tag)
    pysat.logger.info(self.acknowledgements)
    return


def clean(self):
    """Clean the Dst index, empty function."""

    return


# ----------------------------------------------------------------------------
# Instrument functions


def load(fnames, tag='', inst_id=''):
    """Load the Dst index files.

    Parameters
    ----------
    fnames : pandas.Series
        Series of filenames
    tag : str
        Instrument tag string. (default='')
    inst_id : str
        Instrument ID, not used. (default='')

    Returns
    -------
    data : pandas.DataFrame
        Object containing satellite data
    pysat.Meta
        Object containing metadata such as column names and units

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """

    all_data = []

    if tag == 'noaa':
        # NOAA Dst data is actually stored by year, but users can load by day.
        # Extract the actual dates from the input list of filenames as well as
        # the names of the actual files.
        fdates = []
        ufnames = []
        for filename in fnames:
            fdates.append(dt.datetime.strptime(filename[-10:], '%Y-%m-%d'))
            ufnames.append(filename[0:-11])

            # Get unique filenames that map to actual data
            ufnames = np.unique(ufnames).tolist()

        # Load unique files
        for fname in ufnames:
            with open(fname) as open_f:
                lines = open_f.readlines()
                idx = 0

                # Check if all lines are good
                max_lines = 0
                for line in lines:
                    if len(line) > 1:
                        max_lines += 1

                # Prep memory
                yr = np.zeros(max_lines * 24, dtype=int)
                mo = np.zeros(max_lines * 24, dtype=int)
                day = np.zeros(max_lines * 24, dtype=int)
                ut = np.zeros(max_lines * 24, dtype=int)
                dst = np.zeros(max_lines * 24, dtype=int)

                # Read data
                for line in lines:
                    if len(line) > 1:
                        temp_year = np.int64(line[14:16] + line[3:5])
                        if temp_year > 57:
                            temp_year += 1900
                        else:
                            temp_year += 2000

                        yr[idx:idx + 24] = temp_year
                        mo[idx:idx + 24] = np.int64(line[5:7])
                        day[idx:idx + 24] = np.int64(line[8:10])
                        ut[idx:idx + 24] = np.arange(24)
                        temp = line.strip()[20:-4]
                        temp2 = [temp[4 * i:4 * (i + 1)] for i in np.arange(24)]
                        dst[idx:idx + 24] = temp2
                        idx += 24

                # Prep datetime index for the data and create DataFrame
                start = dt.datetime(yr[0], mo[0], day[0], ut[0])
                stop = dt.datetime(yr[-1], mo[-1], day[-1], ut[-1])
                dates = pds.date_range(start, stop, freq='H')
                new_data = pds.DataFrame(dst, index=dates, columns=['dst'])

                # Add to all data loaded for filenames
                all_data.append(new_data)

        # Combine data together
        data = pds.concat(all_data, sort=True, axis=0)

        # Pull out requested days
        data = data.iloc[data.index >= fdates[0], :]
        data = data.iloc[data.index < fdates[-1] + pds.DateOffset(days=1), :]
    else:
        data = pysat.instruments.methods.general.load_csv_data(
            fnames, read_csv_kwargs={'index_col': 0, 'parse_dates': True})

    # Create metadata
    meta = pysat.Meta()
    meta['dst'] = {meta.labels.units: 'nT',
                   meta.labels.name: 'Dst',
                   meta.labels.notes: tags[tag],
                   meta.labels.desc: 'Disturbance storm-time index',
                   meta.labels.fill_val: np.nan,
                   meta.labels.min_val: -np.inf,
                   meta.labels.max_val: np.inf}

    return data, meta


def list_files(tag='', inst_id='', data_path='', format_str=None):
    """List local data files for Dst data.

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
    files : pysat.Files
        A class containing the verified available files

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """
    # Get the format string, if not supplied by the user
    if format_str is None:
        if tag == 'noaa':
            format_str = 'dst{year:4d}.txt'
        else:
            format_str = ''.join(['sw_dst_', tag, '_{year:4d}-{month:2d}-',
                                  '{day:2d}.txt'])

    # Get the desired files
    files = pysat.Files.from_os(data_path=data_path, format_str=format_str)

    if tag == 'noaa':
        # NOAA files yearly, so we need to add daily dates to the yearly
        # filenames. The load routine will load a month of data and use
        # the appended date to select out appropriate data.
        if not files.empty:
            files.loc[files.index[-1] + pds.DateOffset(years=1)
                      - pds.DateOffset(days=1)] = files.iloc[-1]
            files = files.asfreq('D', 'pad')
            files = files + '_' + files.index.strftime('%Y-%m-%d')

    return files


def download(date_array, tag, inst_id, data_path):
    """Download the Dst index data from the appropriate repository.

    Parameters
    ----------
    date_array : array-like or pandas.DatetimeIndex
        Array-like or index of datetimes for which files will be downloaded.
    tag : str
        Instrument tag, used to determine download location.
    inst_id : str
        Instrument ID, not used.
    data_path : str
        Path to data directory.

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """
    if tag == 'noaa':
        # Connect to host, default port
        ftp = ftplib.FTP('ftp.ngdc.noaa.gov')

        # User anonymous, passwd anonymous@
        ftp.login()
        ftp.cwd('/STP/GEOMAGNETIC_DATA/INDICES/DST')

        # Data stored by year. Only download for unique set of input years.
        years = np.array([date.year for date in date_array])
        years = np.unique(years)
        for year in years:
            fname_root = 'dst{year:04d}.txt'
            fname = fname_root.format(year=year)
            saved_fname = os.path.join(data_path, fname)
            try:
                pysat.logger.info('Downloading file for {year:04d}'.format(
                    year=year))
                with open(saved_fname, 'wb') as fp:
                    ftp.retrbinary('RETR ' + fname, fp.write)
            except ftplib.error_perm as exception:
                if str(exception.args[0]).split(" ", 1)[0] != '550':
                    raise
                else:
                    # File not present
                    os.remove(saved_fname)
                    pysat.logger.info('File not available for {:04d}'.format(
                        year))

        ftp.close()
    elif tag == 'lasp':
        # Set the remote data variables
        url = ''.join(['https://lasp.colorado.edu/space_weather/dsttemerin/',
                       'dst_last_96_hrs.txt'])
        times = list()
        data_dict = {'dst': []}

        # Download the webpage
        req = requests.get(url)

        # Test to see if the file was found on the server
        if req.text.find('not found on this server') > 0:
            pysat.logger.warning(''.join(['LASP last 96 hour Dst file not ',
                                          'found on server: ', url]))
        else:
            # Split the file into lines, removing the header and
            # trailing empty line
            file_lines = req.text.split('\n')[1:-1]

            # Format the data
            for line in file_lines:
                # Split the line on whitespace
                line_cols = line.split()

                if len(line_cols) != 2:
                    raise IOError(''.join(['unexpected line encountered in ',
                                           'file retrieved from ', url, ':\n',
                                           line]))

                # Format the time and Dst values
                times.append(dt.datetime.strptime(line_cols[0],
                                                  '%Y/%j-%H:%M:%S'))
                data_dict['dst'].append(np.float64(line_cols[1]))

        # Re-cast the data as a pandas DataFrame
        data = pds.DataFrame(data_dict, index=times)

        # Write out as a file
        file_base = '_'.join(['sw', 'dst', tag, today.strftime('%Y-%m-%d')])
        file_name = os.path.join(data_path, '{:s}.txt'.format(file_base))
        data.to_csv(file_name)

    return
