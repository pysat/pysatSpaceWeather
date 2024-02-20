#!/usr/bin/env python
# -*- coding: utf-8 -*-.
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
#
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
"""Provides support routines for LASP data."""

import datetime as dt
import numpy as np
import os
import pandas as pds
import requests

import pysat


def prediction_downloads(name, tag, data_path, mock_download_dir=None):
    """Download LASP 96-hour prediction data.

    Parameters
    ----------
    name : str
        Instrument name, currently supports Dst, AL, AE, and AU.
    tag : str
        Instrument tag, used to create a descriptive file name.
    data_path : str
        Path to data directory.
    mock_download_dir : str or NoneType
        Local directory with downloaded files or None. If not None, will
        process any files with the correct name and date (following the local
        file prefix and date format) as if they were downloaded (default=None)

    Raises
    ------
    IOError
        If the data link has an unexpected format or an unknown mock download
        directory is supplied.

    """
    times = list()
    data_dict = {name.lower(): []}
    fname = ''.join([name.lower(), '_last_96_hrs.txt'])

    if mock_download_dir is None:
        # Set the remote data variables
        url = ''.join(['https://lasp.colorado.edu/space_weather/dsttemerin/',
                       fname])

        # Download the webpage
        req = requests.get(url)

        # Test to see if the file was found on the server
        if req.text.find('not found on this server') > 0:
            pysat.logger.warning(''.join(['LASP last 96 hour Dst file not ',
                                          'found on server: ', url]))
            raw_txt = None
        else:
            raw_txt = req.text
    else:
        # If a mock download directory was supplied, test to see it exists
        if mock_download_dir is not None:
            if not os.path.isdir(mock_download_dir):
                raise IOError('file location is not a directory: {:}'.format(
                    mock_download_dir))

        # Get the data from the mock download directory
        url = os.path.join(mock_download_dir, fname)
        if os.path.isfile(url):
            with open(url, 'r') as fpin:
                raw_txt = fpin.read()
        else:
            pysat.logger.warning(''.join(['LASP last 96 hour file not found in',
                                          'the local directory: ', url,
                                          ", data may have been saved to an ",
                                          "unexpected filename"]))
            raw_txt = None

    if raw_txt is not None:
        # Split the file into lines, removing the header and
        # trailing empty line
        file_lines = raw_txt.split('\n')[1:-1]

        # Format the data
        for line in file_lines:
            # Split the line on whitespace
            line_cols = line.split()

            if len(line_cols) != 2:
                raise IOError(''.join(['unexpected line encountered in file ',
                                       'retrieved from ', url, ':\n', line]))

            # Format the time and AL values
            times.append(dt.datetime.strptime(line_cols[0], '%Y/%j-%H:%M:%S'))
            data_dict[name.lower()].append(np.float64(line_cols[1]))

    # Re-cast the data as a pandas DataFrame
    data = pds.DataFrame(data_dict, index=times)

    # Write out as a file
    file_base = '_'.join(['sw', name, tag,
                          pysat.utils.time.today().strftime('%Y-%m-%d')])
    file_name = os.path.join(data_path, '{:s}.txt'.format(file_base))
    data.to_csv(file_name)

    return
