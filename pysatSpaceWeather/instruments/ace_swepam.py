# -*- coding: utf-8 -*-
"""Supports ACE Solar Wind Electron Proton Alpha Monitor data.

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
This is not the ACE scientific data set, which will be available at pysatNASA

Examples
--------
The real-time data is stored by generation date, where each file contains the
data for the current day.  If you leave download dates empty, though, it will
grab today's file three times and assign dates from yesterday, today, and
tomorrow.
::


    swepam = pysat.Instrument('ace', 'swepam', tag='realtime')
    swepam.download(start=swepam.today())
    swepam.load(date=swepam.today())

Warnings
--------
The 'realtime' data contains a changing period of time. Loading multiple files,
loading multiple days, the data padding feature, and multi_file_day feature
available from the pyast.Instrument object is not appropriate for 'realtime'
data.

"""

import datetime as dt
import functools
import numpy as np

from pysat.instruments.methods.general import load_csv_data
from pysat import logger

from pysatSpaceWeather.instruments.methods import ace as mm_ace
from pysatSpaceWeather.instruments.methods import general

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

preprocess = general.preprocess


def init(self):
    """Initialize the Instrument object with instrument specific values."""

    # Set the appropraite acknowledgements and references
    self.acknowledgements = mm_ace.acknowledgements()
    self.references = mm_ace.references(self.name)

    logger.info(self.acknowledgements)

    return


def clean(self):
    """Clean real-time ACE data using the status flag.

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

download = functools.partial(mm_ace.download, name=name, now=now)
list_files = functools.partial(mm_ace.list_files, name=name)


def load(fnames, tag='', inst_id=''):
    """Load the ACE space weather prediction data.

    Parameters
    ----------
    fnames : array-like
        Series, list, or array of filenames.
    tag : str
        Instrument tag, not used. (default='')
    inst_id : str
        ACE instrument ID, not used. (default='')

    Returns
    -------
    data : pandas.DataFrame
        Object containing instrument data
    meta : pysat.Meta
        Object containing metadata such as column names and units

    See Also
    --------
    pysat.instruments.methods.general.load_csv_data

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """

    # Save each file to the output DataFrame
    data = load_csv_data(fnames, read_csv_kwargs={'index_col': 0,
                                                  'parse_dates': True})

    # Assign the meta data
    meta, status_desc = mm_ace.common_metadata()
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
