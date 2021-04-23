# -*- coding: utf-8 -*-
"""Supports ACE Solar Wind Electron Proton Alpha Monitor data

Properties
----------
platform
    'ace' Advanced Composition Explorer
name
    'swepam' Solar Wind Electron Proton Alpha Monitor
tag
    - 'realtime' Real-time data from the Space Weather Prediction Center (SWPC)
    - 'historic' Historic data from the SWPC
inst_id
    - ''

Note
----
The real-time data is stored by generation date, where each file contains the
data for the current day.  If you leave download dates empty, though, it will
grab today's file three times and assign dates from yesterday, today, and
tomorrow.
::


    swepam = pysat.Instrument('ace', 'swepam', tag='realtime')
    now = dt.datetime.utcnow()
    swepam.download(start=now)
    swepam.load(date=now)

Warnings
--------
The real-time data should not be used with the data padding option available
from pysat.Instrument objects.

"""

import datetime as dt
import functools
import numpy as np
import pandas as pds

import pysat

from pysatSpaceWeather.instruments.methods import ace as mm_ace

logger = pysat.logger

# ----------------------------------------------------------------------------
# Instrument attributes

platform = 'ace'
name = 'swepam'
tags = {'realtime': 'Real-time data from the SWPC',
        'historic': ' Historic data from the SWPC'}
inst_ids = {inst_id: [tag for tag in tags.keys()] for inst_id in ['']}

# Define today's date
now = dt.datetime.utcnow()

# ----------------------------------------------------------------------------
# Instrument test attributes

# Set test dates (first level: inst_id, second level: tag)
_test_dates = {inst_id: {'realtime': dt.datetime(now.year, now.month, now.day),
                         'historic': dt.datetime(2009, 1, 1)}
               for inst_id in inst_ids.keys()}

# ----------------------------------------------------------------------------
# Instrument methods


def init(self):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.

    """

    # Set the appropraite acknowledgements and references
    self.acknowledgements = mm_ace.acknowledgements()
    self.references = mm_ace.references(self.name)

    logger.info(self.acknowledgements)

    return


def clean(self):
    """Routine to clean real-time ACE data using the status flag

    Note
    ----
    Supports 'clean' and 'dirty'.  Replaces all fill values with NaN.
    Clean - status flag of zero (nominal data)
    Dirty - status flag < 9 (accepts bad data record, removes no data record)

    """
    # Perform the standard ACE cleaning
    max_status = mm_ace.clean(self)

    # Replace bad values with NaN and remove times with no valid data
    self.data = self.data[self.data['status'] <= max_status]

    return


# ----------------------------------------------------------------------------
# Instrument functions

download = functools.partial(mm_ace.download, now=now)
list_files = mm_ace.list_files


def load(fnames, tag=None, inst_id=None):
    """Load the ACE space weather prediction data

    Parameters
    ----------
    fnames : array-like
        Series, list, or array of filenames
    tag : str or NoneType
        tag or None (default=None)
    inst_id : str or NoneType
        ACE instrument or None (default=None)

    Returns
    -------
    data : pandas.DataFrame
        Object containing instrument data
    meta : pysat.Meta
        Object containing metadata such as column names and units

    Raises
    ------
    ValueError
        When unknown inst_id is supplied.

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """

    # Save each file to the output DataFrame
    data = pds.DataFrame()
    for fname in fnames:
        result = pds.read_csv(fname, index_col=0, parse_dates=True)
        data = pds.concat([data, result], axis=0)

    # Assign the meta data
    meta, status_desc = mm_ace.common_meta()
    sw_desc = '1-min averaged Solar Wind '

    meta['status'] = {meta.labels.units: '',
                      meta.labels.name: 'Status',
                      meta.labels.notes: '',
                      meta.labels.desc: status_desc,
                      meta.labels.fill_val: np.nan,
                      meta.labels.min_val: 0,
                      meta.labels.max_val: 9}
    meta['sw_proton_dens'] = {meta.labels.units: 'p/cc',
                              meta.labels.name: 'Solar Wind Proton Density',
                              meta.labels.notes: '',
                              meta.labels.desc: ''.join([sw_desc,
                                                         'Proton Density']),
                              meta.labels.fill_val: -9999.9,
                              meta.labels.min_val: 0.0,
                              meta.labels.max_val: np.inf}
    meta['sw_bulk_speed'] = {meta.labels.units: 'km/s',
                             meta.labels.name: 'Solar Wind Bulk Speed',
                             meta.labels.notes: '',
                             meta.labels.desc: ''.join([sw_desc,
                                                        'Bulk Speed']),
                             meta.labels.fill_val: -9999.9,
                             meta.labels.min_val: -np.inf,
                             meta.labels.max_val: np.inf}
    meta['sw_ion_temp'] = {meta.labels.units: 'K',
                           meta.labels.name: 'Solar Wind Ti',
                           meta.labels.notes: '',
                           meta.labels.desc: ''.join([sw_desc,
                                                      'Ion Temperature']),
                           meta.labels.fill_val: -1.0e5,
                           meta.labels.min_val: 0.0,
                           meta.labels.max_val: np.inf}

    return data, meta


def list_files(tag=None, inst_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for ACE data

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
    pysat.Files.from_os : pysat.utils.files.Files
        A class containing the verified available files

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """

    format_str = '_'.join(["ace", inst_id, tag,
                           '{year:04d}-{month:02d}-{day:02d}.txt'])
    if data_path is not None:
        files = pysat.Files.from_os(data_path=data_path, format_str=format_str)
    else:
        raise ValueError(''.join(('A data_path must be passed to the loading',
                                  ' routine for ACE Space Weather data')))

    return files


def download(date_array, tag, inst_id, data_path):
    """Routine to download ACE Space Weather data

    Parameters
    ----------
    date_array : array-like
        Array of datetime values
    tag : string or NoneType
        Denotes type of file to load. Accepted types are 'realtime' and
        'historic' (default=None)
    inst_id : string or NoneType
        Specifies the ACE instrument. Accepts 'mag', 'sis', 'epam', 'swepam'
    data_path : string or NoneType
        Path to data directory. If None is specified, the value previously
        set in Instrument.files.data_path is used (default=None)

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    Warnings
    --------
    Only able to download current real-time data

    """

    # Define the file information for each data type and check the
    # date range
    if tag == 'realtime':
        file_fmt = "{:s}-{:s}.txt".format("ace", "magnetometer"
                                          if inst_id == "mag" else inst_id)

        if(len(date_array) > 1 or date_array[0].year != now.year
           or date_array[0].month != now.month or date_array[0] != now.day):
            logger.warning('real-time data only available for current day')
    else:
        data_rate = 1 if inst_id in ['mag', 'swepam'] else 5
        file_fmt = '_'.join(["%Y%m%d", "ace", inst_id,
                             '{:d}m.txt'.format(data_rate)])

    url = {'realtime': 'https://services.swpc.noaa.gov/text/',
           'historic': 'https://sohoftp.nascom.nasa.gov/sdb/ace/daily/'}

    data_cols = {'mag': ['jd', 'sec', 'status', 'bx_gsm', 'by_gsm',
                         'bz_gsm', 'bt_gsm', 'lat_gsm', 'lon_gsm'],
                 "swepam": ['jd', 'sec', 'status', 'sw_proton_dens',
                            'sw_bulk_speed', 'sw_ion_temp'],
                 "epam": ['jd', 'sec', 'status_e', 'eflux_38-53',
                          'eflux_175-315', 'status_p', 'pflux_47-68',
                          'pflux_115-195', 'pflux_310-580',
                          'pflux_795-1193', 'pflux_1060-1900', 'anis_ind'],
                 'sis': ['jd', 'sec', 'status_10', 'int_pflux_10MeV',
                         'status_30', 'int_pflux_30MeV']}

    # Cycle through all the dates
    for dl_date in date_array:
        # download webpage
        furl = ''.join((url[tag], dl_date.strftime(file_fmt)))
        req = requests.get(furl)

        # Split the file at the last header line and then by new line markers
        raw_data = req.text.split('#-----------------')[-1]
        raw_data = raw_data.split('\n')[1:]  # Remove the last header line

        # Parse the file, treating the 4 time columns separately
        data_dict = {col: list() for col in data_cols[inst_id]}
        times = list()
        nsplit = len(data_cols[inst_id]) + 4
        for raw_line in raw_data:
            split_line = raw_line.split()
            if len(split_line) == nsplit:
                times.append(dt.datetime.strptime(' '.join(split_line[:4]),
                                                  '%Y %m %d %H%M'))
                for i, col in enumerate(data_cols[inst_id]):
                    # Convert to a number and save
                    #
                    # Output is saved as a float, so don't bother to
                    # differentiate between int and float
                    data_dict[col].append(float(split_line[4 + i]))
            else:
                if len(split_line) > 0:
                    raise IOError(''.join(['unexpected line encoutered in ',
                                           furl, ":\n", raw_line]))

        # put data into nicer DataFrame
        data = pds.DataFrame(data_dict, index=times)

        # write out as a file
        data_file = '{:s}.txt'.format('_'.join(["ace", inst_id, tag,
                                                dl_date.strftime('%Y-%m-%d')]))
        data.to_csv(os.path.join(data_path, data_file), header=True)

    return
