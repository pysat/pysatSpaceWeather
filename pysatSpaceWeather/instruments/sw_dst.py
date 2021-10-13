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

import pysat

from pysatSpaceWeather.instruments.methods import dst as mm_dst

logger = pysat.logger

# ----------------------------------------------------------------------------
# Instrument attributes

platform = 'sw'
name = 'dst'
tags = {'noaa': 'Historic Dst data coalated by and maintained by NOAA/NCEI'}
inst_ids = {'': [tag for tag in tags]}

# ----------------------------------------------------------------------------
# Instrument test attributes

_test_dates = {'': {'noaa': dt.datetime(2007, 1, 1)}}

# Other tags assumed to be True
_test_download_travis = {'': {'noaa': False}}

# ----------------------------------------------------------------------------
# Instrument methods


def init(self):
    """Initialize the Instrument object with instrument specific values."""

    self.acknowledgements = mm_dst.acknowledgements(self.tag)
    self.references = mm_dst.references(self.tag)
    logger.info(self.acknowledgements)
    return


def clean(self):
    """Clean the Dst index, empty function."""

    return


# ----------------------------------------------------------------------------
# Instrument functions


def load(fnames, tag, inst_id):
    """Load the Dst index files.

    Parameters
    ----------
    fnames : pandas.Series
        Series of filenames
    tag : str
        Instrument tag string.
    inst_id : str
        Instrument ID, not used.

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

    # Dst data is actually stored by year but users can load by day.
    # Extract the actual dates from the input list of filenames as
    # well as the names of the actual files.
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
                    temp_year = int(line[14:16] + line[3:5])
                    if temp_year > 57:
                        temp_year += 1900
                    else:
                        temp_year += 2000

                    yr[idx:idx + 24] = temp_year
                    mo[idx:idx + 24] = int(line[5:7])
                    day[idx:idx + 24] = int(line[8:10])
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


def list_files(tag, inst_id, data_path, format_str=None):
    """Return a Pandas Series of every file for chosen satellite data

    Parameters
    ----------
    tag : str
        Instrument tag, accepts any value from `tags`.
    inst_id : str
        Instrument ID, not used.
    data_path : str or NoneType
        Path to data directory.  If None is supplied, raises ValueError.
    format_str : str or NoneType
        User specified file format.  If None is specified, the default
        formats associated with the supplied tags are used. (default=None)

    Returns
    -------
    pysat.Files.from_os : pysat._files.Files
        A class containing the verified available files

    Raises
    ------
    ValueError
        If `data_path` is NoneType or an unknown `tag` is supplied.

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """

    if data_path is not None:
        if tag == 'noaa':
            # files are by year, going to add date to yearly filename for
            # each day of the month. The load routine will load a month of
            # data and use the appended date to select out appropriate data.
            if format_str is None:
                format_str = 'dst{year:4d}.txt'
            out = pysat.Files.from_os(data_path=data_path,
                                      format_str=format_str)
            if not out.empty:
                out.loc[out.index[-1] + pds.DateOffset(years=1)
                        - pds.DateOffset(days=1)] = out.iloc[-1]
                out = out.asfreq('D', 'pad')
                out = out + '_' + out.index.strftime('%Y-%m-%d')
            return out
        else:
            raise ValueError(''.join(('Unrecognized tag name for Space ',
                                      'Weather Dst Index')))
    else:
        raise ValueError(''.join(('A data_path must be passed to the loading ',
                                  'routine for Dst')))
    return


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
            logger.info('Downloading file for {year:04d}'.format(year=year))
            with open(saved_fname, 'wb') as fp:
                ftp.retrbinary('RETR ' + fname, fp.write)
        except ftplib.error_perm as exception:
            if str(exception.args[0]).split(" ", 1)[0] != '550':
                raise
            else:
                # file not present
                os.remove(saved_fname)
                logger.info('File not available for {:04d}'.format(year))

    ftp.close()
    return
