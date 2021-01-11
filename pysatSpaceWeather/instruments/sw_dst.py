# -*- coding: utf-8 -*-
"""Supports Dst values. Downloads data from NGDC.

Properties
----------
platform
    'sw'
name
    'dst'
tag
    None supported

Note
----
Will only work until 2057.

Download method should be invoked on a yearly frequency,
dst.download(date1, date2, freq='AS')

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
tags = {'': ''}
inst_ids = {'': ['']}

# ----------------------------------------------------------------------------
# Instrument test attributes

_test_dates = {'': {'': dt.datetime(2007, 1, 1)}}

# Other tags assumed to be True
_test_download_travis = {'': {'': False}}

# ----------------------------------------------------------------------------
# Instrument methods


def init(self):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.


    """

    self.acknowledgements = mm_dst.acknowledgements(self.name, self.tag)
    self.references = mm_dst.references(self.name, self.tag)
    logger.info(self.acknowledgements)
    return


def clean(self):
    """ Cleaning function for Dst

    Note
    ----
    No necessary for the Dst index

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
    pysat.Meta
        Object containing metadata such as column names and units

    Note
    ----
    Called by pysat. Not intended for direct use by user.


    """

    data = pds.DataFrame()

    for filename in fnames:
        # need to remove date appended to dst filename
        fname = filename[0:-11]
        all_data = []
        with open(fname) as open_f:
            lines = open_f.readlines()
            idx = 0
            # check if all lines are good
            max_lines = 0
            for line in lines:
                if len(line) > 1:
                    max_lines += 1
            yr = np.zeros(max_lines * 24, dtype=int)
            mo = np.zeros(max_lines * 24, dtype=int)
            day = np.zeros(max_lines * 24, dtype=int)
            ut = np.zeros(max_lines * 24, dtype=int)
            dst = np.zeros(max_lines * 24, dtype=int)
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

            start = dt.datetime(yr[0], mo[0], day[0], ut[0])
            stop = dt.datetime(yr[-1], mo[-1], day[-1], ut[-1])
            dates = pds.date_range(start, stop, freq='H')

            new_data = pds.DataFrame(dst, index=dates, columns=['dst'])
            # pull out specific day
            new_date = dt.datetime.strptime(filename[-10:], '%Y-%m-%d')
            idx, = np.where((new_data.index >= new_date)
                            & (new_data.index < new_date
                               + pds.DateOffset(days=1)))
            new_data = new_data.iloc[idx, :]
            # add specific day to all data loaded for filenames
            all_data.append(new_data)
        # combine data together
        data = pds.concat(all_data, sort=True, axis=0)

    return data, pysat.Meta()


def list_files(tag=None, inst_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for chosen satellite data

    Parameters
    ----------
    tag : string or NoneType
        Denotes type of file to load.  Accepted types are '1min' and '5min'.
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


def download(date_array, tag, inst_id, data_path, user=None, password=None):
    """Routine to download Dst index data

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
