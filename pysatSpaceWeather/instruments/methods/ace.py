#!/usr/bin/env python
# -*- coding: utf-8 -*-.
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
# ----------------------------------------------------------------------------
"""Provides general routines for the ACE space weather instruments."""

import datetime as dt
import numpy as np
import os
import pandas as pds
import requests

import pysat

logger = pysat.logger


def acknowledgements():
    """Define the acknowledgements for the specified ACE instrument.

    Returns
    -------
    ackn : str
        Acknowledgements for the ACE instrument

    """

    ackn = ''.join(['NOAA provided funds for the modification of ',
                    ' the ACE transmitter to enable the broadcast of',
                    ' the real-time data and also funds to the ',
                    'instrument teams to provide the algorithms for ',
                    'processing the real-time data.'])

    return ackn


def references(name):
    """Define the references for the specified ACE instrument.

    Parameters
    ----------
    name : str
        Instrument name of the ACE instrument

    Returns
    -------
    ref : str
        Reference for the ACE instrument paper

    """

    refs = {'mag': "".join(["'The ACE Magnetic Field Experiment', ",
                            "C. W. Smith, M. H. Acuna, L. F. Burlaga, ",
                            "J. L'Heureux, N. F. Ness and J. Scheifele, ",
                            "Space Sci. Rev., 86, 613-632 (1998)."]),
            'epam': ''.join(['Gold, R. E., S. M. Krimigis, S. E. Hawkins, ',
                             'D. K. Haggerty, D. A. Lohr, E. Fiore, ',
                             'T. P. Armstrong, G. Holland, L. J. Lanzerotti,',
                             ' Electron, Proton and Alpha Monitor on the ',
                             'Advanced Composition Explorer Spacecraft, ',
                             'Space Sci. Rev., 86, 541, 1998.']),
            'swepam': ''.join(['McComas, D., Bame, S., Barker, P. et al. ',
                               'Solar Wind Electron Proton Alpha Monitor ',
                               '(SWEPAM) for the Advanced Composition ',
                               'Explorer. Space Sci. Rev., 86, 563–612',
                               ' (1998). ',
                               'https://doi.org/10.1023/A:1005040232597']),
            'sis': ''.join(['Stone, E., Cohen, C., Cook, W. et al. The ',
                            'Solar Isotope Spectrometer for the Advanced ',
                            'Composition Explorer. Space Sci. Rev., 86, ',
                            '357–408 (1998). ',
                            'https://doi.org/10.1023/A:1005027929871'])}

    if name not in refs.keys():
        raise KeyError('unknown ACE instrument, accepts {:}'.format(
            refs.keys()))

    return refs[name]


def clean(inst):
    """Clean the common aspects of the ACE space weather data.

    Parameters
    ----------
    inst : pysat.Instrument
        ACE pysat.Instrument object

    Returns
    -------
    max_status : int
        Maximum allowed status

    Note
    ----
    pysat Instrument is modified in place

    """

    if inst.platform != "ace":
        raise AttributeError("Can't apply ACE cleaning to platform {:}".format(
            inst.platform))

    # Set the clean level
    if inst.clean_level == 'dusty':
        logger.warning("unused clean level 'dusty', reverting to 'clean'")
        inst.clean_level = 'clean'

    max_status = 9
    if inst.clean_level == "clean":
        max_status = 0
    elif inst.clean_level == "dirty":
        max_status = 8

    return max_status


def list_files(name, tag='', inst_id='', data_path='', format_str=None):
    """List the local ACE data files.

    Parameters
    ----------
    name : str
        ACE Instrument name.
    tag : str
        ACE Instrument tag. (default='')
    inst_id : str
        Specifies the ACE instrument ID. (default='')
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
    if format_str is None:
        format_str = '_'.join(["ace", name, tag,
                               '{year:04d}-{month:02d}-{day:02d}.txt'])

    files = pysat.Files.from_os(data_path=data_path, format_str=format_str)

    return files


def download(date_array, name, tag='', inst_id='', data_path='', now=None):
    """Download the requested ACE Space Weather data.

    Parameters
    ----------
    date_array : array-like
        Array of datetime values
    name : str
        ACE Instrument name.
    tag : str
        ACE Instrument tag. (default='')
    inst_id : str
        ACE instrument ID. (default='')
    data_path : str
        Path to data directory. (default='')
    now : dt.datetime or NoneType
        Current universal time, if None this is determined for each
        download. (default=None)

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    Warnings
    --------
    - Only able to download current real-time data
    - File requested not available on server

    """

    # Ensure now is up-to-date, if desired
    if now is None:
        now = dt.datetime.utcnow()

    # Define the file information for each data type and check the
    # date range
    if tag == 'realtime':
        file_fmt = "{:s}-{:s}.txt".format("ace", "magnetometer"
                                          if name == "mag" else name)

        if(len(date_array) > 1 or date_array[0].year != now.year
           or date_array[0].month != now.month or date_array[0].day != now.day):
            logger.warning('real-time data only available for current day')
    else:
        data_rate = 1 if name in ['mag', 'swepam'] else 5
        file_fmt = '_'.join(["%Y%m%d", "ace", name,
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
        # Download webpage
        furl = ''.join((url[tag], dl_date.strftime(file_fmt)))
        req = requests.get(furl)

        # Split the file at the last header line and then by new line markers
        raw_data = req.text.split('#-----------------')[-1]
        raw_data = raw_data.split('\n')[1:]  # Remove the last header line

        # Test to see if the file was found on the server
        if ' '.join(raw_data).find('not found on this server') > 0:
            logger.warning('File for {:} not found on server: {:}'.format(
                dl_date.strftime("%d %b %Y"), furl))
        else:
            # Parse the file, treating the 4 time columns separately
            data_dict = {col: list() for col in data_cols[name]}
            times = list()
            nsplit = len(data_cols[name]) + 4
            for raw_line in raw_data:
                split_line = raw_line.split()
                if len(split_line) == nsplit:
                    times.append(dt.datetime.strptime(' '.join(split_line[:4]),
                                                      '%Y %m %d %H%M'))
                    for i, col in enumerate(data_cols[name]):
                        # Convert to a number and save
                        #
                        # Output is saved as a float, so don't bother to
                        # differentiate between int and float
                        data_dict[col].append(float(split_line[4 + i]))
                else:
                    if len(split_line) > 0:
                        raise IOError(''.join(['unexpected line encoutered in ',
                                               furl, ":\n", raw_line]))

            # Put data into nicer DataFrame
            data = pds.DataFrame(data_dict, index=times)

            # Write out as a file
            data_file = '{:s}.txt'.format(
                '_'.join(["ace", name, tag, dl_date.strftime('%Y-%m-%d')]))
            data.to_csv(os.path.join(data_path, data_file), header=True)

    return


def common_metadata():
    """Define the common metadata information for all ACE instruments.

    Returns
    -------
    meta : pysat.Meta
        pysat Meta class with 'jd' and 'sec' initiated
    status_desc : str
        Description of the status flags

    """
    # Initialize the metadata
    meta = pysat.Meta()

    # Define the Julian day
    meta['jd'] = {meta.labels.units: 'days',
                  meta.labels.name: 'MJD',
                  meta.labels.notes: '',
                  meta.labels.desc: 'Modified Julian Day',
                  meta.labels.fill_val: np.nan,
                  meta.labels.min_val: -np.inf,
                  meta.labels.max_val: np.inf}

    # Define the seconds of day
    meta['sec'] = {meta.labels.units: 's',
                   meta.labels.name: 'Sec of Day',
                   meta.labels.notes: '',
                   meta.labels.desc: 'Seconds of Julian Day',
                   meta.labels.fill_val: np.nan,
                   meta.labels.min_val: -np.inf,
                   meta.labels.max_val: np.inf}

    # Provide information about the status flags
    status_desc = '0 = nominal data, 1 to 8 = bad data record, 9 = no data'

    return meta, status_desc


def ace_swepam_hourly_omni_norm(as_inst, speed_key='sw_bulk_speed',
                                dens_key='sw_proton_dens',
                                temp_key='sw_ion_temp'):
    """Normalize ACE SWEPAM variables as described in the OMNI processing _[1].

    Parameters
    ----------
    as_inst : pysat.Instrument
        pysat Instrument object with ACE SWEPAM data.
    speed_key : str
        Data key for bulk solar wind speed data in km/s
        (default='sw_bulk_speed')
    dens_key : str
        Data key for solar wind proton density data in P/cm^3
        (default='sw_proton_dens')
    temp_key : str
        Data key for solar wind ion temperature data in K
        (default='sw_ion_temp')

    References
    ----------
    [1] https://omniweb.gsfc.nasa.gov/html/omni_min_data.html

    """

    # Check the input to make sure all the necessary data variables are present
    for var in [speed_key, dens_key, temp_key]:
        if var not in as_inst.variables:
            raise ValueError('instrument missing variable: {:}'.format(var))

    # Let yt be the fractional years since 1998.0
    yt = np.array([pysat.utils.time.datetime_to_dec_year(itime) - 1998.0
                   for itime in as_inst.index])

    # The normalization depends on the year
    yt_dens = (yt >= 2019.0) & (yt <= 2021.0)
    yt_temp = (yt >= 2019.0) & (yt <= 2020.0)

    # Get the masks for the different velocity limits
    ilow = as_inst[speed_key] < 395
    imid = (as_inst[speed_key] >= 395) & (as_inst[speed_key] <= 405)
    ihigh = as_inst[speed_key] > 405

    # Calculate the normalized plasma density
    norm_n = np.array(as_inst[dens_key])
    norm_n[ilow] *= (0.925 + 0.0039 * yt[ilow])
    norm_n[imid] *= (74.02 - 0.164 * as_inst[speed_key][imid]
                     + 0.0171 * as_inst[speed_key][imid] * yt[imid]
                     - 6.72 * yt[imid]) / 10.0
    norm_n[ihigh] *= (0.761 + 0.0210 * yt[ihigh])

    # Overwrite the calculation for the year where velocity isn't important
    norm_n[yt_dens] = np.power(10.0, -0.010 + 1.006
                               * np.log10(as_inst[dens_key][yt_dens]))

    # Normalize the temperature
    norm_t = np.array(as_inst[temp_key])
    norm_t[~yt_temp] = np.power(10.0,
                                -0.069 + 1.024 * np.log10(norm_t[~yt_temp]))
    norm_t[yt_temp] = np.power(10.0,
                               0.266 + 0.947 * np.log10(norm_t[yt_temp]))

    # Update the instrument data
    as_inst['sw_proton_dens_norm'] = pds.Series(norm_n, index=as_inst.index)
    as_inst['sw_ion_temp_norm'] = pds.Series(norm_t, index=as_inst.index)

    # Add meta data
    for dkey in [dens_key, temp_key]:
        nkey = '{:s}_norm'.format(dkey)
        meta_dict = {}

        for mkey in as_inst.meta[dkey].keys():
            if mkey == as_inst.meta.labels.notes:
                meta_dict[mkey] = ''.join([
                    'Normalized for hourly OMNI as described in ',
                    'https://omniweb.gsfc.nasa.gov/html/omni_min_data.html'])
            elif mkey != "children":
                meta_dict[mkey] = as_inst.meta[dkey, mkey]

        as_inst.meta[nkey] = meta_dict

    return
