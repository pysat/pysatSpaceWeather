#!/usr/bin/env python
# -*- coding: utf-8 -*-.
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
# ----------------------------------------------------------------------------
"""Supports the MgII core-to-wing ratio index.

Properties
----------
platform
    'sw'
name
    'mgii'
tag
    - 'composite' Composite data set of MgII core-to-wing index
    - 'sorce' SORCE SOLSTICE MgII core-to-wing index

Examples
--------
Download a month of the composite MgII data and load the second day of the
month.
::

    stime = dt.datetime(1981, 2, 2)
    mgii = pysat.Instrument('sw', 'mgii', tag='composite')
    mgii.download(start=stime)
    mgii.load(date=stime)

"""

import datetime as dt
import numpy as np
import pandas as pds

import pysat

from pysatSpaceWeather.instruments.methods import general
from pysatSpaceWeather.instruments.methods import lisird


# ----------------------------------------------------------------------------
# Instrument attributes

platform = 'sw'
name = 'mgii'
tags = {'composite': 'Composite data set of MgII core-to-wing index',
        'sorce': 'SORCE SOLSTICE MgII core-to-wing index'}

# Dict keyed by inst_id that lists supported tags for each inst_id
inst_ids = {'': [tag for tag in tags.keys()]}

# Dict keyed by inst_id that lists supported tags and a good day of test data
# generate todays date to support loading forecast data
now = dt.datetime.utcnow()
today = dt.datetime(now.year, now.month, now.day)
tomorrow = today + pds.DateOffset(days=1)

# ----------------------------------------------------------------------------
# Instrument test attributes

_test_dates = {'': {'composite': dt.datetime(1981, 11, 6),
                    'sorce': dt.datetime(2005, 3, 6)}}

# ----------------------------------------------------------------------------
# Instrument methods

preprocess = general.preprocess


def init(self):
    """Initialize the Instrument object with instrument specific values."""

    # Set the required Instrument attributes
    self.acknowledgements = lisird.ackn
    self.references = lisird.references(self.platform, self.name, self.tag,
                                        self.inst_id)
    pysat.logger.info(self.acknowledgements)

    return


def clean(self):
    """Clean the MGII data, empty function as this is not necessary."""

    if self.tag == 'sorce':
        pysat.logger.warning(''.join(["The SORCE MGII core-to-wing ratio has ",
                                      "an associated uncertaintly ('unc') ",
                                      "that should be considered when using ",
                                      'the data']))
    return


# ----------------------------------------------------------------------------
# Instrument functions


def load(fnames, tag='', inst_id=''):
    """Load MGII core-to-wing ratio index files.

    Parameters
    ----------
    fnames : pandas.Series
        Series of filenames.
    tag : str
        Instrument tag. (default='')
    inst_id : str
        Instrument ID, not used. (default='')

    Returns
    -------
    data : pandas.DataFrame
        Object containing satellite data.
    meta : pysat.Meta
        Object containing metadata such as column names and units.

    See Also
    --------
    pysat.instruments.methods.general.load_csv_data

    """
    # Get the desired file dates and file names from the daily indexed list
    file_dates = list()
    if tag == 'composite':
        unique_files = list()
        for fname in fnames:
            file_dates.append(dt.datetime.strptime(fname[-10:], '%Y-%m-%d'))
            if fname[0:-11] not in unique_files:
                unique_files.append(fname[0:-11])
        fnames = unique_files

    # Load the CSV data files
    data = pysat.instruments.methods.general.load_csv_data(
        fnames, read_csv_kwargs={"index_col": 0, "parse_dates": True})

    # If there is a date range, downselect here
    if len(file_dates) > 0:
        idx, = np.where((data.index >= min(file_dates))
                        & (data.index < max(file_dates) + dt.timedelta(days=1)))
        data = data.iloc[idx, :]

    # Initalize the metadata
    meta = pysat.Meta()
    notes = {
        'composite': ''.join([
            'The Mg II Index is a proxy for solar chromospheric variability. ',
            'This composite data record is based on the work of Viereck et ',
            'al. (2004) Space Weather, vol 2, CiteID S10005 for measurements',
            ' from 1978 through 2003. For this time range, the Upper ',
            'Atmosphere Research Satellite (UARS) Solar Ultraviolet Spectral ',
            'Irradiance Monitor (SUSIM), UARS Solar Stellar Irradiance ',
            'Comparison Experiment (SOLSTICE), ERS-2/Global Ozone Monitoring ',
            'Experiment (GOME) and five NOAA solar backscatter ultraviolet ',
            'data sets were used. Initially, the best data sets were ',
            'selected. Then the gaps in the record were filled with data ',
            'from various other Mg II data sets. Where no alternate data were',
            ' available, a cubic spline function was used to bridge the ',
            'missing data. In some cases the data gaps were too long for ',
            'reasonable spline fits (more than 5 days), and for these gaps ',
            'the F10.7 cm flux data were scaled to fill the gaps.\nStarting ',
            'in 2003, the data from SORCE SOLSTICE is used exclusively. The ',
            'SOLSTICE spectra have been convolved with a 1.1 nm triangular ',
            'response function to improve the long-term agreement with other ',
            'measurements. All of the data sets have been normalized to a ',
            'commonscale to create a single long-term record.\nFor more ',
            'details please see https://lasp.colorado.edu/home/sorce/',
            'instruments/solstice/solstice-data-product-release-notes/.']),
        'sorce': ''.join([
            'The SORCE Magnesium II core-to-wing index is produced from SORCE',
            ' SOLSTICE instrument measurements using the definition in Snow ',
            'et al. [2005]. The spectral resolution of SORCE SOLSTICE (0.1 ',
            'nm) allows the emission cores of the Mg II doublet to be fully ',
            'resolved and modeled with Gaussian functions. To determine the ',
            'wing irradiances, the spectrum is convolved with a 1.1 nm ',
            'triangular bandpass and then measured at the four wavelengths ',
            'used by NOAA as described in Heath and Schlesinger [1986]. This',
            ' method has several advantages; most importantly it extracts a ',
            'more precise measurement of solar activity [Snow et al., 2005]. ',
            'A simple linear correlation with the standard NOAA data product ',
            'can be used to scale this SORCE measurement to be compatible ',
            'with the long-term composite Mg II index maintained by NOAA.'])}
    meta['mg_index'] = {meta.labels.units: '',
                        meta.labels.name: 'MG II index',
                        meta.labels.notes: notes[tag],
                        meta.labels.desc: 'MG II core-to-wing ratio index',
                        meta.labels.fill_val: np.nan,
                        meta.labels.min_val: 0,
                        meta.labels.max_val: np.inf}

    if 'unc' in data.columns:
        meta['unc'] = {meta.labels.units: '',
                       meta.labels.name: 'MG II Index Uncertainty',
                       meta.labels.notes: "".join([
                           "As described in Snow et al. (2005), the formal ",
                           "uncertainty in each SOLSTICE MgII index ",
                           "measurement is about 0.65%. This is derived from ",
                           "the statistical uncertainty of the underlying ",
                           "spectral measurements and the way they are ",
                           "combined to produce the index."]),
                       meta.labels.desc:
                       'MG II core-to-wing ratio index uncertainty',
                       meta.labels.fill_val: np.nan,
                       meta.labels.min_val: 0,
                       meta.labels.max_val: np.inf}

    return data, meta


def list_files(tag='', inst_id='', data_path='', format_str=None):
    """List local MGII core-to-wing ratio index files.

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
    out_files : pysat._files.Files
        A class containing the verified available files

    Note
    ----
    Called by pysat. Not intended for direct use by user.

    """

    # If the format string is not supplied, build the default string
    if format_str is None:
        format_str = "".join([
            "mgii_", tag, "_{year:04d}-{month:02d}",
            '.txt' if tag == 'composite' else '-{day:02d}.txt'])

    # Get the files using the default function
    out_files = pysat.Files.from_os(data_path=data_path, format_str=format_str)

    if tag == 'composite':
        # Files are by month, going to add date to monthly filename for
        # each day of the month. The load routine will load a month of
        # data and use the appended date to select out appropriate data.
        if not out_files.empty:
            out_files.loc[out_files.index[-1] + pds.DateOffset(months=1)
                          - pds.DateOffset(days=1)] = out_files.iloc[-1]
            out_files = out_files.asfreq('D', 'pad')
            out_files = out_files + '_' + out_files.index.strftime(
                '%Y-%m-%d')

    return out_files


def download(date_array, tag, inst_id, data_path):
    """Download MGII core-to-wing index data from the appropriate repository.

    Parameters
    ----------
    date_array : array-like
        Sequence of dates for which files will be downloaded.
    tag : str
        Denotes type of file to load.
    inst_id : str
        Specifies the ID for the Instrument (not used).
    data_path : str
        Path to data directory.

    Raises
    ------
    IOError
        If a problem is encountered connecting to the gateway or retrieving
        data from the repository.

    """

    # Set the download input options
    local_file_prefix = "mgii_{:s}_".format(tag)
    lisird_data_name = "{:s}_mg_index".format(tag)

    if tag == "composite":
        local_file_prefix = "mgii_composite_"
        local_date_fmt = "%Y-%m"
        freq = pds.DateOffset(months=1, seconds=-1)

        # Adjust the date array if monthly downloads are desired
        if date_array.freq != 'MS':
            date_array = pysat.utils.time.create_date_range(
                dt.datetime(date_array[0].year, date_array[0].month, 1),
                date_array[-1], freq='MS')

    elif tag == "sorce":
        local_date_fmt = "%Y-%m-%d"
        freq = dt.timedelta(seconds=86399)

    # Download the desired data
    lisird.download(date_array, data_path, local_file_prefix, local_date_fmt,
                    lisird_data_name, freq)

    return
