# -*- coding: utf-8 -*-.
"""Provides general routines for the ACE space weather instruments
"""

import datetime as dt
import numpy as np
import os
import pandas as pds
import requests

import pysat

logger = pysat.logger


def acknowledgements():
    """Returns acknowledgements for the specified ACE instrument

    Returns
    -------
    ackn : string
        Acknowledgements for the ACE instrument

    """

    ackn = ''.join(['NOAA provided funds for the modification of ',
                    ' the ACE transmitter to enable the broadcast of',
                    ' the real-time data and also funds to the ',
                    'instrument teams to provide the algorithms for ',
                    'processing the real-time data.'])

    return ackn


def references(name):
    """Returns references for the specified ACE instrument

    Parameters
    ----------
    name : string
        Instrument name of the ACE instrument

    Returns
    -------
    ref : string
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
    """Common aspects of the ACE space weather data cleaning

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


def list_files(name='', tag='', inst_id='', data_path='', format_str=None):
    """Return a Pandas Series of every file for ACE data

    Parameters
    ----------
    name : str
        ACE Instrument name. (default='')
    tag : str
        Denotes type of file to load. (default='')
    inst_id : str
        Specifies the ACE instrument ID. (default='')
    data_path : str
        Path to data directory. (default='')
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
    if format_str is None:
        format_str = '_'.join(["ace", name, tag,
                               '{year:04d}-{month:02d}-{day:02d}.txt'])

    files = pysat.Files.from_os(data_path=data_path, format_str=format_str)

    return files


def download(date_array, name='', tag='', inst_id='', data_path='', now=None):
    """Routine to download ACE Space Weather data

    Parameters
    ----------
    date_array : array-like
        Array of datetime values
    name : str
        ACE Instrument name. (default='')
    tag : str
        Denotes type of file to load. Accepted types are 'realtime' and
        'historic'. (default='')
    inst_id : str
        Specifies the ACE instrument ID. (default='')
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
    """Provides common metadata information for all ACE instruments

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


def load_csv_data(fnames, read_csv_kwargs=None):
    """Load CSV data from a list of files into a single DataFrame

    Parameters
    ----------
    fnames : array-like
        Series, list, or array of filenames
    read_csv_kwargs : dict or NoneType
        Dict of kwargs to apply to `pds.read_csv`. (default=None)

    Returns
    -------
    data : pds.DataFrame
        Data frame with data from all files in the fnames list

    See Also
    --------
    pds.read_csv

    """
    # Ensure the filename input is array-like
    fnames = np.asarray(fnames)
    if fnames.shape == ():
        fnames = np.asarray([fnames])

    # Initialize the optional kwargs
    if read_csv_kwargs is None:
        read_csv_kwargs = {}

    # Create a list of data frames from each file
    fdata = []
    for fname in fnames:
        fdata.append(pds.read_csv(fname, **read_csv_kwargs))

    data = pds.DataFrame() if len(fdata) == 0 else pds.concat(fdata, axis=0)
    return data
