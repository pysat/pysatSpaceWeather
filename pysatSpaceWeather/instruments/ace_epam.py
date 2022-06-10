# -*- coding: utf-8 -*-
"""Supports ACE Electron, Proton, and Alpha Monitor data.

Properties
----------
platform
    'ace' Advanced Composition Explorer
name
    'epam' Electron, Proton, and Alpha Monitor
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

    epam = pysat.Instrument('ace', 'epam', tag='realtime')
    epam.download(start=epam.today())
    epam.load(date=epam.today())



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
name = 'epam'
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

    # Set the appropriate acknowledgements and references
    self.acknowledgements = mm_ace.acknowledgements()
    self.references = mm_ace.references(self.name)

    logger.info(self.acknowledgements)

    return


def clean(self):
    """Clean the real-time ACE data using the status flag.

    Note
    ----
    Supports 'clean' and 'dirty'.  Replaces all fill values with NaN.
    Clean - status flag of zero (nominal data)
    Dirty - status flag < 9 (accepts bad data record, removes no data record)

    """
    # Perform the standard ACE cleaning
    max_status = mm_ace.clean(self)

    # Replace bad values with NaN and remove times with no valid data
    ecols = ['eflux_38-53', 'eflux_175-315']

    # Evaluate the electron flux data
    self[self.data['status_e'] > max_status, ecols] = np.nan

    # Evaluate the proton flux data
    pcols = ['pflux_47-68', 'pflux_115-195', 'pflux_310-580',
             'pflux_795-1193', 'pflux_1060-1900']
    self[self.data['status_p'] > max_status, pcols] = np.nan

    # Include both fluxes and the anisotropy index in the removal eval
    eval_cols = ecols + pcols
    eval_cols.append('anis_ind')

    # Remove lines without any good data
    good_cols = (np.isfinite(self.data.loc[:, eval_cols])).sum(axis=1)
    bad_index = good_cols[good_cols == 0].index
    self.data = self.data.drop(index=bad_index)

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
        Instrument tag (default='').
    inst_id : str
        ACE instrument ID (default='').

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
    flux_desc = '5-min averaged Differential '

    meta['status_e'] = {meta.labels.units: '',
                        meta.labels.name: 'Diff e- Flux Status',
                        meta.labels.notes: '',
                        meta.labels.desc: status_desc,
                        meta.labels.fill_val: np.nan,
                        meta.labels.min_val: 0,
                        meta.labels.max_val: 9}
    meta['status_p'] = {meta.labels.units: '',
                        meta.labels.name: 'Diff Proton Flux Status',
                        meta.labels.notes: '',
                        meta.labels.desc: status_desc,
                        meta.labels.fill_val: np.nan,
                        meta.labels.min_val: 0,
                        meta.labels.max_val: 9}
    meta['anis_ind'] = {meta.labels.units: '',
                        meta.labels.name: 'Anisotropy Index',
                        meta.labels.notes: '',
                        meta.labels.desc: 'Range: 0.0 - 2.0',
                        meta.labels.fill_val: -1.0,
                        meta.labels.min_val: 0.0,
                        meta.labels.max_val: 2.0}
    meta['eflux_38-53'] = {meta.labels.units: 'particles/cm2-s-ster-MeV',
                           meta.labels.name: 'Diff e- Flux 38-53 eV',
                           meta.labels.notes: '',
                           meta.labels.desc:
                           ''.join([flux_desc,
                                    'Electron Flux between 35-53 eV']),
                           meta.labels.fill_val: -1.0e5,
                           meta.labels.min_val: -np.inf,
                           meta.labels.max_val: np.inf}
    meta['eflux_175-315'] = {meta.labels.units: 'particles/cm2-s-ster-MeV',
                             meta.labels.name: 'Diff e- Flux 175-315 eV',
                             meta.labels.notes: '',
                             meta.labels.desc:
                             ''.join([flux_desc,
                                      'Electron Flux between 175-315 eV']),
                             meta.labels.fill_val: -1.0e5,
                             meta.labels.min_val: -np.inf,
                             meta.labels.max_val: np.inf}
    meta['pflux_47-68'] = {meta.labels.units: 'particles/cm2-s-ster-MeV',
                           meta.labels.name: 'Diff Proton Flux 47-68 keV',
                           meta.labels.notes: '',
                           meta.labels.desc:
                           ''.join([flux_desc,
                                    'Proton Flux between 47-68 keV']),
                           meta.labels.fill_val: -1.0e5,
                           meta.labels.min_val: -np.inf,
                           meta.labels.max_val: np.inf}
    meta['pflux_115-195'] = {meta.labels.units: 'particles/cm2-s-ster-MeV',
                             meta.labels.name: 'Diff Proton Flux 115-195 keV',
                             meta.labels.notes: '',
                             meta.labels.desc:
                             ''.join([flux_desc,
                                      'Proton Flux between 115-195 keV']),
                             meta.labels.fill_val: -1.0e5,
                             meta.labels.min_val: -np.inf,
                             meta.labels.max_val: np.inf}
    meta['pflux_310-580'] = {meta.labels.units: 'particles/cm2-s-ster-MeV',
                             meta.labels.name: 'Diff Proton Flux 310-580 keV',
                             meta.labels.notes: '',
                             meta.labels.desc:
                             ''.join([flux_desc,
                                      'Proton Flux between 310-580 keV']),
                             meta.labels.fill_val: -1.0e5,
                             meta.labels.min_val: -np.inf,
                             meta.labels.max_val: np.inf}
    meta['pflux_795-1193'] = {meta.labels.units: 'particles/cm2-s-ster-MeV',
                              meta.labels.name: 'Diff Proton Flux 795-1193 keV',
                              meta.labels.notes: '',
                              meta.labels.desc:
                              ''.join([flux_desc,
                                       'Proton Flux between 795-1193 keV']),
                              meta.labels.fill_val: -1.0e5,
                              meta.labels.min_val: -np.inf,
                              meta.labels.max_val: np.inf}
    meta['pflux_1060-1900'] = {meta.labels.units: 'particles/cm2-s-ster-MeV',
                               meta.labels.name:
                               'Diff Proton Flux 1060-1900 keV',
                               meta.labels.notes: '',
                               meta.labels.desc:
                               ''.join([flux_desc,
                                        'Proton Flux between 1060-1900 keV']),
                               meta.labels.fill_val: -1.0e5,
                               meta.labels.min_val: -np.inf,
                               meta.labels.max_val: np.inf}
    return data, meta
