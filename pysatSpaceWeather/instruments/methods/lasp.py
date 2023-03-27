# -*- coding: utf-8 -*-.
"""Provides support routines for LASP data."""

import datetime as dt
import numpy as np
import os
import pandas as pds
import requests

import pysat


def prediction_downloads(name, tag, data_path):
    """Download LASP 96-hour prediction data.

    Parameters
    ----------
    name : str
        Instrument name, currently supports Dst, AL, AE, and AU.
    tag : str
        Instrument tag, used to create a descriptive file name.
    data_path : str
        Path to data directory.

    Raises
    ------
    IOError
        If the data link has an unexpected format

    """

    # Set the remote data variables
    url = ''.join(['https://lasp.colorado.edu/space_weather/dsttemerin/',
                   name.lower(), '_last_96_hrs.txt'])
    times = list()
    data_dict = {name.lower(): []}

    # Download the webpage
    req = requests.get(url)

    # Test to see if the file was found on the server
    if req.text.find('not found on this server') > 0:
        pysat.logger.warning(''.join(['LASP last 96 hour Dst file not ',
                                      'found on server: ', url]))
    else:
        # Split the file into lines, removing the header and
        # trailing empty line
        file_lines = req.text.split('\n')[1:-1]

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
