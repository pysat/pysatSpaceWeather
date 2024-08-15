#!/usr/bin/env python
# -*- coding: utf-8 -*-.
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
# ----------------------------------------------------------------------------
"""Supports data from the Nobeyama Radio Polarimeters."""

import datetime as dt
import numpy as np
import os
import pandas as pds
import requests

import pysat


def acknowledgements():
    """Define the acknowledgements for NoRP data.

    Returns
    -------
    ackn : str
        Acknowledgements associated with the appropriate NoRP name and tag.

    """
    ackn = ''.join(['The Nobeyama Radio Polarimeters (NoRP) are operated by ',
                    'Solar Science Observatory, a branch of National ',
                    'Astronomical Observatory of Japan, and their observing ',
                    'data are verified scientifically by the consortium for ',
                    'NoRP scientific operations.',
                    '\nFor questions regarding the data please contact ',
                    'solar_helpdesk@ml.nao.ac.jp'])

    return ackn


def references(name, tag):
    """Define the references for NoRP data.

    Parameters
    ----------
    name : str
        Instrument name for the NoRP data.
    tag : str
        Instrument tag for the NoRP data.

    Returns
    -------
    refs : str
        Reference string associated with the appropriate F10.7 tag.

    """
    refs = {'rf': {'daily': "\n".join([
        ''.join(['Shimojo and Iwai "Over seven decades of solar microwave ',
                 'data obtained with Toyokawa and Nobeyama Radio Polarimeters',
                 '", GDJ, 10, 114-129 (2023)']),
        ''.join(['Nakajima et al. "The Radiometer and Polarimeters at 80, 35,',
                 ' and 17 GHz for Solar Observations at Nobeyama", PASJ, 37,',
                 ' 163 (1985)']),
        ''.join(['Torii et al. "Full-Automatic Radiopolarimeters for Solar ',
                 'Patrol at Microwave Frequencies", Proc. of the Res. Inst. ',
                 'of Atmospherics, Nagoya Univ., 26, 129 (1979)']),
        ''.join(['Shibasaki et al. "Solar Radio Data Acquisition and ',
                 'Communication System (SORDACS) of Toyokawa Observatory", ',
                 'Proc. of the Res. Inst. of Atmospherics, Nagoya Univ., 26, ',
                 '117 (1979)']),
        'Tanaka, "Toyokawa Observatory", Solar Physics, 1, 2, 295 (1967)',
        ''.join(['Tsuchiya and Nagase "Atmospheric Absorption in Microwave ',
                 'Solar Observation and Solar Flux Measurement at 17 Gc/s", ',
                 'PASJ, 17, 86 (1965)']),
        ''.join(['Tanaka and Kakinuma. "EQUIPMENT FOR THE OBSERVATION OF SOLAR',
                 ' RADIO EMISSION AT 9400, 3750, 2000 AND 1000 Mc/s", Proc. ',
                 'of the Res. Inst. of Atmospherics, Nagoya Univ., 4, 60 ',
                 '(1957)']),
        ''.join(['Tanaka et al. "EQUIPMENT FOR THE OBSERVATION OF SOLAR NOISE ',
                 'AT 3,750 MC", Proc. of the Res. Inst. of Atmospherics, ',
                 'Nagoya Univ., 1, 71 (1953)'])])}}

    return refs[name][tag]


def daily_rf_downloads(data_path, mock_download_dir=None, start=None,
                       stop=None):
    """Download LASP 96-hour prediction data.

    Parameters
    ----------
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

    Note
    ----
    Saves data in month-long files

    """
    # Initalize the output information
    times = list()
    data_dict = dict()

    # Set the file name
    fname = 'TYKW-NoRP_dailyflux.txt'

    if mock_download_dir is None:
        # Set the remote data variables
        url = '/'.join(['https://solar.nro.nao.ac.jp/norp/data/daily', fname])

        # Download the webpage
        req = requests.get(url)

        # Test to see if the file was found on the server
        if req.text.find('not found on this server') > 0:
            pysat.logger.warning(''.join(['NoRP daily flux file not found on ',
                                          'server: ', url]))
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
            pysat.logger.warning(''.join(['NoRP daily flux file not found in',
                                          'the local directory: ', url,
                                          ", data may have been saved to an ",
                                          "unexpected filename"]))
            raw_txt = None

    if raw_txt is not None:
        # Split the text to get the header lines
        file_lines = raw_txt.split('\n')[:2]

        # If needed, set or adjust the start and end times
        line_cols = file_lines[0].split()
        file_start = dt.datetime.strptime(line_cols[-3], '(%Y-%m-%d')
        file_stop = dt.datetime.strptime(line_cols[-1], '%Y-%m-%d)')

        # Evaluate the file start time
        if start is None or start < file_start:
            start = file_start
        elif start.day > 1:
            # Set the start time to be the start of the month
            start = dt.datetime(start.year, start.month, 1)

        # Evaluate the file stop time
        if stop is None or stop < file_stop:
            stop = file_stop
        elif stop.day < 31:
            # Set the stop time to be the end of the month
            month_end = stop + dt.timedelta(days=1)
            while month_end.month == stop.month:
                stop = dt.datetime(month_end.year, month_end.month,
                                   month_end.day)
                month_end += dt.timedelta(days=1)

        # Set the data columns
        data_cols = [col.replace(" ", "_") for col in file_lines[1].split(',')]
        for col in data_cols[1:]:
            data_dict[col] = list()

        # Split the text to get the file line for the desired period
        start_txt = raw_txt.split(start.strftime('"%Y-%m-%d"'))[1]
        stop_txt = ''.join([start.strftime('"%Y-%m-%d"'), start_txt]).split(
            stop.strftime('"%Y-%m-%d"'))
        file_lines = stop_txt[0].split('\n')[:-1]
        if len(stop_txt) > 1:
            file_lines.append(''.join([stop.strftime('"%Y-%m-%d"'),
                                       stop_txt[1]]).split('\n')[0])

        # Format the data for the desired time period
        for line in file_lines:
            # Split the line on comma
            line_cols = line.split(',')

            if len(line_cols) != len(data_cols):
                raise IOError(''.join(['unexpected line encountered in file ',
                                       'retrieved from ', url, ':\n', line]))

            # Format the time and values
            times.append(dt.datetime.strptime(line_cols[0], '"%Y-%m-%d"'))
            for i, col in enumerate(data_cols[1:]):
                if line_cols[i + 1].lower().find('nan') == 0:
                    data_dict[col].append(np.nan)
                else:
                    data_dict[col].append(np.float64(line_cols[i + 1]))

        # Re-cast the data as a pandas DataFrame
        data = pds.DataFrame(data_dict, index=times)

        # Write out the files using a monthly cadance
        file_base = '_'.join(['norp', 'rf', 'daily', '%Y-%m.txt'])

        while start < stop:
            # Set the output file name
            file_name = os.path.join(data_path, start.strftime(file_base))

            # Downselect the output data
            file_data = data[start:start + pds.DateOffset(months=1)
                             - dt.timedelta(microseconds=1)]

            # Save the output data to file
            file_data.to_csv(file_name)

            # Cycle the time
            start += pds.DateOffset(months=1)

    return
