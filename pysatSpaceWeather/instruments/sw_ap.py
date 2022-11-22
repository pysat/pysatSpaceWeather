# -*- coding: utf-8 -*-
"""Supports ap index values.

Properties
----------
platform
    'sw'
name
    'ap'
tag
    - 'def' Definitive ap data from GFZ
    - 'now' Nowcast ap data from GFZ
    - 'recent' Grab last 30 days of Ap data from SWPC
inst_id
    ''

Note
----
Downloads data from ftp.gfz-potsdam.de or SWPC. These files also contain Kp
data (with the GFZ data additionally containing Cp data), and so the additional
data files will be saved to the appropriate data directories to avoid multiple
downloads.

The historic definitive and nowcast Kp files are stored in yearly files, with
the current year being updated remotely on a regular basis.  If you are using
historic data for the current year, we recommend re-downloading it before
performing your data processing.

Recent data is also stored by the generation date from the SWPC. Each file
contains 30 days of Ap measurements. The load date issued to pysat corresponds
to the generation date.

Examples
--------
::

    ap = pysat.Instrument('sw', 'ap', tag='recent')
    ap.download()
    ap.load(date=ap.tomorrow())


Warnings
--------
The 'recent' tag loads Ap data for a specific period of time. Loading multiple
files, loading multiple days, the data padding feature, and multi_file_day
feature available from the pyast.Instrument object is not appropriate for this
tag data.

"""

import datetime as dt
import numpy as np
import pandas as pds

import pysat

from pysatSpaceWeather.instruments.methods import general
from pysatSpaceWeather.instruments.methods import kp_ap

# ----------------------------------------------------------------------------
# Instrument attributes

platform = 'sw'
name = 'ap'
tags = {'def': 'Definitive Kp data from GFZ',
        'now': 'Nowcast Kp data from GFZ',
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
                    'recent': today}}

# ----------------------------------------------------------------------------
# Instrument methods

preprocess = general.preprocess


def init(self):
    """Initialize the Instrument object with instrument specific values."""

    self.acknowledgements = kp_ap.acknowledgements(self.name, self.tag)
    self.references = kp_ap.references(self.name, self.tag)
    pysat.logger.info(self.acknowledgements)
    return


def clean(self):
    """Clean the Kp, not required for this index (empty function)."""

    return


# ----------------------------------------------------------------------------
# Instrument functions


def load(fnames, tag='', inst_id=''):
    """Load Ap index files.

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

    """

    meta = pysat.Meta()
    if tag in ['def', 'now']:
        # Load the definitive or nowcast data. The Ap data stored in yearly
        # files, and we need to return data daily.  The daily date is
        # attached to filename.  Parse off the last date, load month of data,
        # and downselect to the desired day
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

        # Initalize the meta data
        fill_val = np.nan
        for kk in result.keys():
            if kk.lower().find('ap') >= 0:
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
    else:
        # Load the recent data
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

    """

    if tag in ['def', 'now']:
        files = kp_ap.gfz_kp_ap_cp_list_files(name, tag, inst_id, data_path,
                                              format_str=format_str)
    else:
        files = kp_ap.swpc_list_files(name, tag, inst_id, data_path,
                                      format_str=format_str)

    return files


def download(date_array, tag, inst_id, data_path):
    """Download the Ap index data from the appropriate repository.

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
    Only able to download current recent data, not archived forecasts.

    """

    if tag in ['def', 'now']:
        kp_ap.gfz_kp_ap_cp_download(platform, name, tag, inst_id, date_array,
                                    data_path)
    else:
        kp_ap.swpc_kp_ap_recent_download(name, date_array, data_path)

    return
