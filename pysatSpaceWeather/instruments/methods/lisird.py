#!/usr/bin/env python
# -*- coding: utf-8 -*-.
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
#
# Review Status for Classified or Controlled Information by NRL
# -------------------------------------------------------------
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
"""Provides support functions for the LASP LISIRD data base."""

import datetime as dt
import json
import numpy as np
import os
import pandas as pds
import requests

import pysat

ackn = "".join(["LASP Interactive Solar Irradiance Data Center provides ",
                "access to many solar datasets generated by researchers at ",
                "LASP and other institutions."])


def references(platform, name, tag, inst_id):
    """Provide references for different Instrument data products.

    Parameters
    ----------
    platform : str
        Instrument platform
    name : str
        Instrument name
    tag : str
        Instrument tag
    inst_id : str
        Instrument ID

    Returns
    -------
    refs : str
        String of references

    """

    refs = {'sw': {'mgii': {
        'composite': {
            '': ''.join(["Viereck, R. A., Floyd, L. E., Crane, P. C., Woods, ",
                         "T. N., Knapp, B. G., Rottman, G., Weber, M., Puga,",
                         " L. C., and DeLand, M. T. (2004), A composite Mg ",
                         "II index spanning from 1978 to 2003, Space Weather",
                         ", 2, S10005, doi:10.1029/2004SW000084."])},
        'sorce': {
            '': "\n".join([
                "".join(["Snow, M, William E. McClintock, Thomas N. Woods, ",
                         "Oran R. White, Jerald W. Harder, and Gary Rottman ",
                         "(2005). The Mg II Index from SORCE, Solar Phys., ",
                         "230, 1, 325-344."]),
                "".join(["Heath, D. and Schlesinger, B. (1986). The Mg 280-nm ",
                         "doublet as a monitor of changes in solar ",
                         "ultraviolet irradiance, JGR, 91, 8672-8682."])])}}}}

    return refs[platform][name][tag][inst_id]


def build_lisird_url(lisird_data_name, start, stop):
    """Build a LASP LISIRD direct download URL.

    Parameters
    ----------
    lisird_data_name : str
        Name of the data set on the LISARD server
    start : dt.datetime
        Start time
    stop : dt.datetime
        Stop time

    Returns
    -------
    url : str
        URL that will download the desired data

    """

    # Define the formatting for the start and stop times
    tfmt = "%Y-%m-%dT%H:%M:%S.000Z"

    url = "".join(["https://lasp.colorado.edu/lisird/latis/dap/",
                   lisird_data_name, ".json?&time>=", start.strftime(tfmt),
                   '&time<=', stop.strftime(tfmt),
                   "&format_time(yyyy-MM-dd'T'HH:mm:ss.SSS)"])

    return url


def download(date_array, data_path, local_file_prefix, local_date_fmt,
             lisird_data_name, freq, update_files=False, fill_vals=None,
             mock_download_dir=None):
    """Download routine for LISIRD data.

    Parameters
    ----------
    date_array : array-like
        Sequence of dates for which files will be downloaded.
    data_path : str
        Path to data directory.
    local_file_prefix : str
        Prefix for local files, e.g., 'tag_' or 'tag_monthly_'
    local_date_fmt : str
        String format for the local filename, e.g., '%Y-%m-%d' or '%Y-%m'
    lisird_data_name : str
        Name of the data set on the LISARD server
    freq : pds.DateOffset or dt.timedelta
        Offset to add to the start date to ensure all data is downloaded
        (inclusive)
    update_files : bool
        Re-download data for files that already exist if True (default=False)
    fill_vals : dict or NoneType
        Dict of fill values to replace with NaN by variable name or None to
        leave alone (default=None)
    mock_download_dir : str or NoneType
        Local directory with downloaded files or None. If not None, will
        process any files with the correct name and date (following the local
        file prefix and date format) as if they were downloaded (default=None)

    Raises
    ------
    IOError
        If there is a gateway timeout when downloading data or an unknown mock
        download directory is supplied.
    KeyError
        If the `fill_vals` input does not match the downloaded data.

    """
    # If a mock download directory was supplied, test to see it exists
    if mock_download_dir is not None:
        if not os.path.isdir(mock_download_dir):
            raise IOError('file location is not a directory: {:}'.format(
                mock_download_dir))

    # Initialize the fill_vals dict, if necessary
    if fill_vals is None:
        fill_vals = {}

    # Cycle through all the dates
    for dl_date in date_array:
        # Build the local filename
        fname = ''.join([local_file_prefix, dl_date.strftime(local_date_fmt),
                         '.txt'])
        local_file = os.path.join(data_path, fname)

        # Determine if the download should occur
        if update_files or not os.path.isfile(local_file):
            if mock_download_dir is None:
                # Get the URL for the desired data
                url = build_lisird_url(lisird_data_name, dl_date,
                                       dl_date + freq)

                # The data is returned as a JSON file
                req = requests.get(url)

                # Process the JSON file
                if req.text.find('Gateway Timeout') >= 0:
                    raise IOError(''.join(['Gateway timeout when requesting ',
                                           'file using command: ', url]))

                # Load the dict if text was retrieved
                json_dict = json.loads(req.text) if req.ok else {'': {}}
            else:
                # Get the local repository filename
                url = os.path.join(mock_download_dir, fname)
                if os.path.isfile(url):
                    with open(url, 'r') as fpin:
                        raw_txt = fpin.read()

                    json_dict = json.loads(raw_txt)
                else:
                    json_dict = {'': {}}

            if lisird_data_name in json_dict.keys():
                raw_dict = json_dict[lisird_data_name]
                data = pds.DataFrame.from_dict(raw_dict['samples'])
                if data.empty:
                    pysat.logger.warning("no data for {:}".format(dl_date))
                else:
                    # The URL specifies the time format, so break it down
                    frac_sec = [int(tval.split('.')[-1])
                                for tval in data['time']]
                    times = [dt.datetime.strptime(tval.split('.')[0],
                                                  '%Y-%m-%dT%H:%M:%S')
                             + dt.timedelta(microseconds=frac_sec[i] * 6)
                             for i, tval in enumerate(data.pop('time'))]
                    data.index = times

                    # Replace fill value with NaNs
                    for var in fill_vals.keys():
                        if var in data.columns:
                            idx, = np.where(data[var] == fill_vals[var])
                            data.iloc[idx, :] = np.nan
                        else:
                            raise KeyError(''.join(['unknown fill value ',
                                                    'variable name supplied: ',
                                                    var]))

                    # Create a local CSV file
                    data.to_csv(local_file, header=True)
            else:
                if len(json_dict.keys()) == 1 and '' in json_dict.keys():
                    pysat.logger.info("".join(["Data not downloaded for ",
                                               dl_date.strftime("%d %b %Y"),
                                               ", date may be out of range ",
                                               "for the database or data may ",
                                               "have been saved to an ",
                                               "unexpected filename: ", url]))
                else:
                    raise IOError(''.join(['Returned unexpectedly formatted ',
                                           'data using command: ', url]))
    return
