# -*- coding: utf-8 -*-
"""Supports ACE Magnetometer data

Properties
----------
platform
    'sw'
name
    'ace'
tag
    - 'realtime' Real-time data from the Space Weather Prediction Center (SWPC)
    - 'historic' Historic data from the SWPC
sat_id
    - 'mag' Magnetometer
    - 'swepam' Solar Wind Electron Proton Alpha Monitor
    - 'sis' Solar Isotope Spectrometer
    - 'epam' Electron, Proton, and Alpha Monitor

Note
----
The real-time data is stored by generation date, where each file contains the
data for the current day.  If you leave download dates empty, though, it will
grab today's file three times and assign dates from yesterday, today, and
tomorrow.
::

    mag = pysat.Instrument('sw', 'ace', sat_id='mag', tag='realtime')
    mag.download(start=dt.datetime.now(), stop=dt.datetime.now())
    mag.load(date=dt.datetime.now())



Warnings
--------
The real-time data should not be used with the data padding option available
from pysat.Instrument objects.

"""

import datetime as dt
import logging
import numpy as np
import os
import requests

import pandas as pds

import pysat
import pysatSpaceWeather.instruments.methods.ace as mm_ace

logger = logging.getLogger(__name__)

# Define the Instrument platform, name, tags, and sat_ids
platform = 'sw'
name = 'ace'
tags = {'realtime': 'Real-time data from the SWPC',
        'historic': ' Historic data from the SWPC'}
sat_ids = {sat_id: [tag for tag in tags.keys()]
           for sat_id in ['mag', 'swepam', 'epam', 'sis']}

# Define today's date
now = dt.datetime.now()

# set test dates (first level: sat_id, second level: tag)
_test_dates = {sat_id: {'realtime': dt.datetime(now.year, now.month, now.day),
                        'historic': dt.datetime(2009, 1, 1)}
               for sat_id in sat_ids.keys()}


def init(self):
    """Initializes the Instrument object with instrument specific values.

    Runs once upon instantiation.

    """

    # Set the appropraite acknowledgements and references
    self.acknowledgements = mm_ace.acknowledgements(self.platform)
    self.references = mm_ace.references(self.sat_id)

    logger.info(self.acknowledgements)

    return


def load(fnames, tag=None, sat_id=None):
    """Load the ACE space weather prediction data

    Parameters
    ----------
    fnames : array-like
        Series, list, or array of filenames
    tag : str or NoneType
        tag or None (default=None)
    sat_id : str or NoneType
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
        When unknown sat_id is supplied.

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
    meta = pysat.Meta()
    meta['jd'] = {meta.units_label: 'days',
                  meta.name_label: 'MJD',
                  meta.desc_label: 'Modified Julian Day'}
    meta['sec'] = {meta.units_label: 's',
                   meta.name_label: 'Sec of Day',
                   meta.desc_label: 'Seconds of Julian Day'}
    status_desc = '0 = nominal data, 1 to 8 = bad data record, 9 = no data'

    if sat_id == 'mag':
        meta['status'] = {meta.name_label: 'Status',
                          meta.desc_label: status_desc}
        meta['bx_gsm'] = {meta.units_label: 'nT',
                          meta.name_label: 'Bx GSM',
                          meta.desc_label: '1-min averaged IMF Bx',
                          meta.fill_label: -999.9}
        meta['by_gsm'] = {meta.units_label: 'nT',
                          meta.name_label: 'By GSM',
                          meta.desc_label: '1-min averaged IMF By',
                          meta.fill_label: -999.9}
        meta['bz_gsm'] = {meta.units_label: 'nT',
                          meta.name_label: 'Bz GSM',
                          meta.desc_label: '1-min averaged IMF Bz',
                          meta.fill_label: -999.9}
        meta['bt_gsm'] = {meta.units_label: 'nT',
                          meta.name_label: 'Bt GSM',
                          meta.desc_label: '1-min averaged IMF Bt',
                          meta.fill_label: -999.9}
        meta['lat_gsm'] = {meta.units_label: 'degrees',
                           meta.name_label: 'GSM Lat',
                           meta.desc_label: 'GSM Latitude',
                           meta.fill_label: -999.9,
                           meta.min_label: -90.0, meta.max_label: 90.0}
        meta['lon_gsm'] = {meta.units_label: 'degrees',
                           meta.name_label: 'GSM Lon',
                           meta.desc_label: 'GSM Longitude',
                           meta.fill_label: -999.9,
                           meta.min_label: 0.0, meta.max_label: 360.0}
    elif sat_id == 'epam':
        flux_desc = '5-min averaged Differential '
        meta['status_e'] = {meta.name_label: 'Diff e- Flux Status',
                            meta.desc_label: status_desc}
        meta['status_p'] = {meta.name_label: 'Diff Proton Flux Status',
                            meta.desc_label: status_desc}
        meta['anis_ind'] = {meta.name_label: 'Anisotropy Index',
                            meta.desc_label: 'Range: 0.0 - 2.0',
                            meta.fill_label: -1.0}
        meta['eflux_38-53'] = {meta.units_label: 'particles/cm2-s-ster-MeV',
                               meta.name_label: 'Diff e- Flux 38-53 eV',
                               meta.desc_label:
                               ''.join([flux_desc,
                                        'Electron Flux between 35-53 eV']),
                               meta.fill_label: -1.0e5}
        meta['eflux_175-315'] = {meta.units_label: 'particles/cm2-s-ster-MeV',
                                 meta.name_label: 'Diff e- Flux 175-315 eV',
                                 meta.desc_label:
                                 ''.join([flux_desc,
                                          'Electron Flux between 175-315 eV']),
                                 meta.fill_label: -1.0e5}
        meta['pflux_47-68'] = {meta.units_label: 'particles/cm2-s-ster-MeV',
                               meta.name_label: 'Diff Proton Flux 47-68 keV',
                               meta.desc_label:
                               ''.join([flux_desc,
                                        'Proton Flux between 47-68 keV']),
                               meta.fill_label: -1.0e5}
        meta['pflux_115-195'] = {meta.units_label: 'particles/cm2-s-ster-MeV',
                                 meta.name_label:
                                 'Diff Proton Flux 115-195 keV',
                                 meta.desc_label:
                                 ''.join([flux_desc,
                                          'Proton Flux between 115-195 keV']),
                                 meta.fill_label: -1.0e5}
        meta['pflux_310-580'] = {meta.units_label: 'particles/cm2-s-ster-MeV',
                                 meta.name_label:
                                 'Diff Proton Flux 310-580 keV',
                                 meta.desc_label:
                                 ''.join([flux_desc,
                                          'Proton Flux between 310-580 keV']),
                                 meta.fill_label: -1.0e5}
        meta['pflux_795-1193'] = {meta.units_label: 'particles/cm2-s-ster-MeV',
                                  meta.name_label:
                                  'Diff Proton Flux 795-1193 keV',
                                  meta.desc_label:
                                  ''.join([flux_desc,
                                           'Proton Flux between 795-1193 ',
                                           'keV']),
                                  meta.fill_label: -1.0e5}
        meta['pflux_1060-1900'] = {meta.units_label: 'particles/cm2-s-ster-MeV',
                                   meta.name_label:
                                   'Diff Proton Flux 1060-1900 keV',
                                   meta.desc_label:
                                   ''.join([flux_desc,
                                            'Proton Flux between 1060-1900',
                                            ' keV']),
                                   meta.fill_label: -1.0e5}
    elif sat_id == "swepam":
        sw_desc = '1-min averaged Solar Wind '
        meta['status'] = {meta.name_label: 'Status',
                          meta.desc_label: status_desc}
        meta['sw_proton_dens'] = {meta.units_label: 'p/cc',
                                  meta.name_label: 'Solar Wind Proton Density',
                                  meta.desc_label: ''.join([sw_desc,
                                                            'Proton Density']),
                                  meta.fill_label: -9999.9}
        meta['sw_bulk_speed'] = {meta.units_label: 'km/s',
                                 meta.name_label: 'Solar Wind Bulk Speed',
                                 meta.desc_label: ''.join([sw_desc,
                                                           'Bulk Speed']),
                                 meta.fill_label: -9999.9}
        meta['sw_ion_temp'] = {meta.units_label: 'K',
                               meta.name_label: 'Solar Wind Ti',
                               meta.desc_label: ''.join([sw_desc,
                                                         'Ion Temperature']),
                               meta.fill_label: -1.0e5}
    elif sat_id == 'sis':
        flux_name = 'Integral Proton Flux'
        meta['status_10'] = {meta.name_label: ''.join([flux_name,
                                                       ' > 10 MeV Status']),
                             meta.desc_label: status_desc}
        meta['status_30'] = {meta.name_label: ''.join([flux_name,
                                                       ' > 30 MeV Status']),
                             meta.desc_label: status_desc}
        meta['int_pflux_10MeV'] = {meta.units_label: 'p/cs2-sec-ster',
                                   meta.name_label: ''.join([flux_name,
                                                             ' > 10 MeV']),
                                   meta.desc_label: ''.join(['5-min averaged ',
                                                             flux_name,
                                                             ' > 10 MeV']),
                                   meta.fill_label: -1.0e5}
        meta['int_pflux_30MeV'] = {meta.units_label: 'p/cs2-sec-ster',
                                   meta.name_label: ''.join([flux_name,
                                                             ' > 30 MeV']),
                                   meta.desc_label: ''.join(['5-min averaged ',
                                                             flux_name,
                                                             ' > 30 MeV']),
                                   meta.fill_label: -1.0e5}
    else:
        raise ValueError('unknown sat_id {:}'.format(sat_id))

    return data, meta


def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Return a Pandas Series of every file for ACE data

    Parameters
    ----------
    tag : string or NoneType
        Denotes type of file to load.
        (default=None)
    sat_id : string or NoneType
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

    format_str = '_'.join(["ace", sat_id, tag,
                           '{year:04d}-{month:02d}-{day:02d}.txt'])
    if data_path is not None:
        files = pysat.Files.from_os(data_path=data_path, format_str=format_str)
    else:
        raise ValueError(''.join(('A data_path must be passed to the loading',
                                  ' routine for ACE Space Weather data')))

    return files


def download(date_array, tag, sat_id, data_path):
    """Routine to download ACE Space Weather data

    Parameters
    ----------
    date_array : array-like
        Array of datetime values
    tag : string or NoneType
        Denotes type of file to load. Accepted types are 'realtime' and
        'historic' (default=None)
    sat_id : string or NoneType
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
                                          if sat_id == "mag" else sat_id)

        if(len(date_array) > 1 or date_array[0].year != now.year or
           date_array[0].month != now.month or date_array[0] != now.day):
            logging.warning('real-time data only available for current day')
    else:
        data_rate = 1 if sat_id in ['mag', 'swepam'] else 5
        file_fmt = '_'.join(["%Y%m%d", "ace", sat_id,
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
        data_dict = {col: list() for col in data_cols[sat_id]}
        times = list()
        nsplit = len(data_cols[sat_id]) + 4
        for raw_line in raw_data:
            split_line = raw_line.split()
            if len(split_line) == nsplit:
                times.append(dt.datetime.strptime(' '.join(split_line[:4]),
                                                  '%Y %m %d %H%M'))
                for i, col in enumerate(data_cols[sat_id]):
                    # Convert to a number and save
                    #
                    # Output is saved as a float, so don't bother to
                    # differentiate between int and float
                    data_dict[col].append(float(split_line[4+i]))
            else:
                if len(split_line) > 0:
                    raise IOError(''.join(['unexpected line encoutered in ',
                                           furl, ":\n", raw_line]))

        # put data into nicer DataFrame
        data = pds.DataFrame(data_dict, index=times)

        # write out as a file
        data_file = '{:s}.txt'.format('_'.join(["ace", sat_id, tag,
                                                dl_date.strftime('%Y-%m-%d')]))
        data.to_csv(os.path.join(data_path, data_file), header=True)

    return


def clean(self):
    """Routine to clean real-time ACE data using the status flag

    Note
    ----
    Supports 'clean' and 'dirty'.  Replaces all fill values with NaN.
    Clean - status flag of zero (nominal data)
    Dirty - status flag < 9 (accepts bad data record, removes no data record)

    """

    # Set the clean level
    if self.clean_level == 'dusty':
        logger.warning("unused clean level 'dusty', reverting to 'clean'")
        self.clean_level = 'clean'

    max_status = 9
    if self.clean_level == "clean":
        max_status = 0
    elif self.clean_level == "dirty":
        max_status = 8

    # Replace all fill values with NaN
    for col in self.data.columns:
        fill_val = self.meta[col][self.meta.fill_label]
        if ~np.isnan(fill_val):
            self.data[col] = self.data[col].replace(fill_val, np.nan)

    # Replace bad values with NaN and remove times with no valid data
    if self.sat_id in ['mag', 'swepam']:
        self.data = self.data[self.data['status'] <= max_status]
    else:
        if self.sat_id == 'epam':
            ecols = ['eflux_38-53', 'eflux_175-315']
            # Evaluate the electron flux data
            for col in ecols:
                self.data[col][self.data['status_e'] > max_status] = np.nan

            # Evaluate the proton flux data
            pcols = ['pflux_47-68', 'pflux_115-195', 'pflux_310-580',
                     'pflux_795-1193', 'pflux_1060-1900']
            for col in pcols:
                self.data[col][self.data['status_p'] > max_status] = np.nan

            # Include both fluxes and the anisotropy index in the removal eval
            eval_cols = ecols + pcols
            eval_cols.append('anis_ind')
        elif self.sat_id == 'sis':
            # Evaluate the different proton fluxes
            self.data['int_pflux_10MeV'][
                self.data['status_10'] > max_status] = np.nan
            self.data['int_pflux_30MeV'][
                self.data['status_30'] > max_status] = np.nan

            eval_cols = ['int_pflux_10MeV', 'int_pflux_30MeV']
        else:
            raise ValueError('unknown sat_id {:}'.format(self.sat_id))

        # Remove lines without any good data
        good_cols = (~np.isnan(self.data.loc[:, eval_cols])).sum(axis=1)
        bad_index = good_cols[good_cols == 0].index
        self.data = self.data.drop(index=bad_index)

    return
