#!/usr/bin/env python
# -*- coding: utf-8 -*-.
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
#
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
"""Provides routines that support SWPC space weather instruments."""

import datetime as dt
import ftplib
import numpy as np
import os
import pandas as pds
import sys

import pysat

from pysatSpaceWeather.instruments.methods import general

# ----------------------------------------------------------------------------
# Define the module variables

ackn = ''.join(['Prepared by the U.S. Dept. of Commerce, NOAA, Space ',
                'Weather Prediction Center'])
forecast_warning = ''.join(['This routine can only download the current ',
                            'forecast, not archived forecasts'])


# ----------------------------------------------------------------------------
# Define the module functions

def daily_dsd_download(name, today, data_path, mock_download_dir=None):
    """Download the daily NOAA Daily Solar Data indices.

    Parameters
    ----------
    name : str
        Instrument name, expects one of 'f107', 'flare', 'ssn', or 'sbfield'.
    today : dt.datetime
        Datetime for current day.
    data_path : str
        Path to data directory.
    mock_download_dir : str or NoneType
        Local directory with downloaded files or None. If not None, will
        process any files with the correct name and date as if they were
        downloaded (default=None)

    Raises
    ------
    IOError
        If an unknown mock download directory is supplied or the desired file
        is missing.

    Note
    ----
    Note that the download path for the complementary Instrument will use
    the standard pysat data paths

    """
    pysat.logger.info('This routine only downloads the latest 30 day file')

    # Get the file information
    raw_txt = general.get_local_or_remote_text(
        'https://services.swpc.noaa.gov/text/', mock_download_dir,
        'daily-solar-indices.txt')

    if raw_txt is None:
        pysat.logger.info("".join(["Data not downloaded for ",
                                   "daily-solar-indices.txt, data may have ",
                                   "been saved to an unexpected filename."]))
    else:
        # Get the file paths and output names
        file_paths = {data_name: data_path if name == data_name else
                      general.get_instrument_data_path(
                          'sw_{:s}'.format(data_name), tag='daily')
                      for data_name in ['f107', 'flare', 'ssn', 'sbfield']}
        outfiles = {
            data_name: os.path.join(file_paths[data_name], '_'.join([
                data_name, 'daily', '{:s}.txt'.format(
                    today.strftime('%Y-%m-%d'))]))
            for data_name in file_paths.keys()}

        # Check that the directories exist
        for data_path in file_paths.values():
            pysat.utils.files.check_and_make_path(data_path)

        # Save the output
        rewrite_daily_solar_data_file(today.year, outfiles, raw_txt)

    return


def old_indices_dsd_download(name, date_array, data_path, local_files, today,
                             mock_download_dir=None):
    """Download the old NOAA Daily Solar Data indices.

    Parameters
    ----------
    name : str
        Instrument name, expects one of 'f107', 'flare', 'ssn', or 'sbfield'.
    date_array : array-like or pandas.DatetimeIndex
        Array-like or index of datetimes to be downloaded.
    data_path : str
        Path to data directory.
    local_files : pds.Series
        A Series containing the local filenames indexed by time.
    today : dt.datetime
        Datetime for current day
    mock_download_dir : str or NoneType
        Local directory with downloaded files or None. If not None, will
        process any files with the correct name and date as if they were
        downloaded (default=None)

    Raises
    ------
    IOError
        If an unknown mock download directory is supplied.

    Note
    ----
    Note that the download path for the complementary Instrument will use
    the standard pysat data paths

    """
    # Get the file paths
    file_paths = {data_name: data_path if name == data_name else
                  general.get_instrument_data_path('sw_{:s}'.format(data_name),
                                                   tag='prelim')
                  for data_name in ['f107', 'flare', 'ssn', 'sbfield']}

    # Check that the directories exist
    for data_path in file_paths.values():
        pysat.utils.files.check_and_make_path(data_path)

    if mock_download_dir is None:
        # Connect to the host, default port
        ftp = ftplib.FTP('ftp.swpc.noaa.gov')
        ftp.login()  # User anonymous, passwd anonymous
        ftp.cwd('/pub/indices/old_indices')
    elif not os.path.isdir(mock_download_dir):
        raise IOError('file location is not a directory: {:}'.format(
            mock_download_dir))

    bad_fname = list()

    # To avoid downloading multiple files, cycle dates based on file length
    dl_date = date_array[0]
    while dl_date <= date_array[-1]:
        # The file name changes, depending on how recent the requested data is
        qnum = (dl_date.month - 1) // 3 + 1  # Integer floor division
        qmonth = (qnum - 1) * 3 + 1
        quar = 'Q{:d}_'.format(qnum)
        fnames = ['{:04d}{:s}DSD.txt'.format(dl_date.year, ss)
                  for ss in ['_', quar]]
        versions = ["01_v2", "{:02d}_v1".format(qmonth)]
        vend = [dt.datetime(dl_date.year, 12, 31),
                dt.datetime(dl_date.year, qmonth, 1)
                + pds.DateOffset(months=3) - pds.DateOffset(days=1)]
        downloaded = False
        rewritten = False

        # Attempt the download(s)
        for iname, fname in enumerate(fnames):
            # Test to see if we already tried this filename
            if fname in bad_fname:
                continue

            local_fname = fname
            saved_fname = os.path.join(data_path, local_fname)
            outfiles = {
                data_name: os.path.join(file_paths[data_name], '_'.join(
                    [data_name, 'prelim', '{:04d}'.format(dl_date.year),
                     '{:s}.txt'.format(versions[iname])]))
                for data_name in file_paths.keys()}

            if os.path.isfile(outfiles[name]):
                downloaded = True

                # Check the date to see if this should be rewritten
                checkfile = os.path.split(outfiles[name])[-1]
                has_file = local_files == checkfile
                if np.any(has_file):
                    if has_file[has_file].index[-1] < vend[iname]:
                        # This file will be updated again, but only attempt to
                        # do so if enough time has passed from the last time it
                        # was downloaded
                        yesterday = today - pds.DateOffset(days=1)
                        if has_file[has_file].index[-1] < yesterday:
                            rewritten = True
            else:
                # The file does not exist, if it can be downloaded, it
                # should be 'rewritten'
                rewritten = True

            # Attempt to download if the file does not exist or if the
            # file has been updated
            if rewritten or not downloaded:
                if mock_download_dir is None:
                    try:
                        sys.stdout.flush()
                        ftp.retrbinary('RETR ' + fname,
                                       open(saved_fname, 'wb').write)
                        downloaded = True
                        pysat.logger.info(' '.join(('Downloaded file for ',
                                                    dl_date.strftime('%x'))))

                    except ftplib.error_perm as exception:
                        # Could not fetch, so cannot rewrite
                        rewritten = False

                        # Test for an error
                        if str(exception.args[0]).split(" ", 1)[0] != '550':
                            raise IOError(exception)
                        else:
                            # File isn't actually there, try the next name.  The
                            # extra wrapping is for Windows, which can encounter
                            # permission errors when handling files.
                            attempt = 0
                            while attempt < 100:
                                try:
                                    os.remove(saved_fname)
                                    attempt = 100
                                except PermissionError:
                                    attempt += 1

                            # Save this so we don't try again. Because there are
                            # two possible filenames for each time, it's ok if
                            # one isn't there.  We just don't want to keep
                            # looking for it.
                            bad_fname.append(fname)
                else:
                    # Set the saved filename
                    saved_fname = os.path.join(mock_download_dir, local_fname)
                    downloaded = True

                    if os.path.isfile(saved_fname):
                        rewritten = True
                    else:
                        pysat.logger.info("".join([saved_fname, "is missing, ",
                                                   "data may have been saved ",
                                                   "to an unexpected ",
                                                   "filename."]))
                        rewritten = False

            # If the first file worked, don't try again
            if downloaded:
                break

        if not downloaded:
            pysat.logger.info(' '.join(('File not available for',
                                        dl_date.strftime('%x'))))
        elif rewritten:
            with open(saved_fname, 'r') as fprelim:
                lines = fprelim.read()

            rewrite_daily_solar_data_file(dl_date.year, outfiles, lines)
            if mock_download_dir is None:
                # Only remove the file if it wasn't obtained from a local dir
                os.remove(saved_fname)

        # Cycle to the next date
        dl_date = vend[iname] + pds.DateOffset(days=1)

    # Close connection after downloading all dates
    if mock_download_dir is None:
        ftp.close()
    return


def rewrite_daily_solar_data_file(year, outfiles, lines):
    """Rewrite the SWPC Daily Solar Data files.

    Parameters
    ----------
    year : int
        Year of data file (format changes based on date)
    outfiles : dict
        Output filenames for all relevant Instruments
    lines : str
        String containing all output data (result of 'read')

    """

    # Get to the solar index data
    if year > 2000:
        raw_data = lines.split('#---------------------------------')[-1]
        raw_data = raw_data.split('\n')[1:-1]
        optical = True
    else:
        raw_data = lines.split('# ')[-1]
        raw_data = raw_data.split('\n')
        optical = False if raw_data[0].find('Not Available') or year == 1994 \
            else True
        istart = 7 if year < 2000 else 1
        raw_data = raw_data[istart:-1]

    # Parse the data
    solar_times, data_dict = parse_daily_solar_data(raw_data, year, optical)

    # Separate data by Instrument name
    data_cols = {'f107': ['f107'],
                 'flare': ['goes_bgd_flux', 'c_flare', 'm_flare', 'x_flare',
                           'o1_flare', 'o2_flare', 'o3_flare', 'o1_flare',
                           'o2_flare', 'o3_flare', 'c_flare', 'm_flare',
                           'x_flare'],
                 'ssn': ['ssn', 'ss_area', 'new_reg'],
                 'sbfield': ['smf']}

    for data_name in data_cols.keys():
        name_dict = {dkey: data_dict[dkey] for dkey in data_dict.keys()
                     if dkey in data_cols[data_name]}

        # Collect into DataFrame
        data = pds.DataFrame(name_dict, index=solar_times)

        # Write out as a file
        data.to_csv(outfiles[data_name], header=True)

    return


def parse_daily_solar_data(data_lines, year, optical):
    """Parse the data in the SWPC daily solar index file.

    Parameters
    ----------
    data_lines : list
        List of lines containing data
    year : list
        Year of file
    optical : boolean
        Flag denoting whether or not optical data is available

    Returns
    -------
    dates : list
        List of dates for each date/data pair in this block
    values : dict
        Dict of lists of values, where each key is the value name

    """

    # Initialize the output
    dates = list()
    val_keys = ['f107', 'ssn', 'ss_area', 'new_reg', 'smf', 'goes_bgd_flux',
                'c_flare', 'm_flare', 'x_flare', 'o1_flare', 'o2_flare',
                'o3_flare']
    optical_keys = ['o1_flare', 'o2_flare', 'o3_flare']
    xray_keys = ['c_flare', 'm_flare', 'x_flare']
    values = {kk: list() for kk in val_keys}

    # Cycle through each line in this file
    for line in data_lines:
        # Split the line on whitespace
        split_line = line.split()

        # Format the date
        dfmt = "%Y %m %d" if year > 1996 else "%d %b %y"
        dates.append(dt.datetime.strptime(" ".join(split_line[0:3]), dfmt))

        # Format the data values
        j = 0
        for i, kk in enumerate(val_keys):
            if year == 1994 and kk == 'new_reg':
                # New regions only in files after 1994
                val = -999
            elif np.any([year == 1994 and kk in xray_keys,
                         not optical and kk in optical_keys]):
                # X-ray flares in files after 1994, optical flares come later
                val = -1
            else:
                val = split_line[j + 3]
                j += 1

            if kk != 'goes_bgd_flux':
                if val == "*":
                    val = -999 if i < 5 else -1
                else:
                    val = int(val)
            values[kk].append(val)

    return dates, values


def solar_geomag_predictions_download(name, date_array, data_path,
                                      mock_download_dir=None):
    """Download the 3-day solar-geomagnetic predictions from SWPC.

    Parameters
    ----------
    name : str
        Instrument name, expects one of 'kp', 'ap', 'stormprob', 'f107',
        'flare', or 'polarcap'.
    date_array : array-like or pandas.DatetimeIndex
        Array-like or index of datetimes to be downloaded.
    data_path : str
        Path to data directory.
    mock_download_dir : str or NoneType
        Local directory with downloaded files or None. If not None, will
        process any files with the correct name and date as if they were
        downloaded (default=None)

    Raises
    ------
    IOError
        If an unknown mock download directory is supplied or the desired file
        is missing.

    Note
    ----
    Note that the download path for the complementary Instrument will use
    the standard pysat data paths

    """
    pysat.logger.info(forecast_warning)

    # Get the file paths
    file_paths = {data_name: data_path if name == data_name else
                  general.get_instrument_data_path(
                      'sw_{:s}'.format(data_name),
                      tag='forecast' if data_name == 'f107' else 'prediction')
                  for data_name in ['kp', 'ap', 'stormprob', 'f107', 'flare',
                                    'polarcap']}

    # Check that the directories exist
    for data_path in file_paths.values():
        pysat.utils.files.check_and_make_path(data_path)

    # Get the file information
    raw_txt = general.get_local_or_remote_text(
        'https://services.swpc.noaa.gov/text/', mock_download_dir,
        '3-day-solar-geomag-predictions.txt')

    if raw_txt is None:
        pysat.logger.info("".join(["Data not downloaded for ",
                                   "3-day-solar-geomag-predictions.txt, data ",
                                   "may have been saved to an unexpected ",
                                   "filename."]))
    else:
        # Parse text to get the date the prediction was generated
        date_str = raw_txt.split(':Issued: ')[-1].split(' UTC')[0]
        dl_date = dt.datetime.strptime(date_str, '%Y %b %d %H%M')

        # Parse the data to get the prediction dates
        date_strs = raw_txt.split(':Prediction_dates:')[-1].split('\n')[0]
        pred_times = [
            dt.datetime.strptime(' '.join(date_str.split()), '%Y %b %d')
            for date_str in date_strs.split('  ') if len(date_str) > 0]

        # Separate out the data by chunks
        ap_raw = raw_txt.split(':Geomagnetic_A_indices:')[-1]
        kp_raw = raw_txt.split(':Pred_Mid_k:')[-1]
        storm_raw = raw_txt.split(':Prob_Mid:')[-1]
        pc_raw = raw_txt.split(':Polar_cap:')[-1]
        f107_raw = raw_txt.split(':10cm_flux:')[-1]
        flare_raw = raw_txt.split(':Whole_Disk_Flare_Prob:')[-1]

        # Initalize the data for each data type
        data_vals = {data_name: dict() for data_name in file_paths.keys()}
        data_times = {data_name: pred_times for data_name in file_paths.keys()}

        # Process the ap data
        for line in ap_raw.split('\n'):
            if line.find(":") == 0:
                break
            elif line.find("A_") == 0:
                split_line = line.split()
                if split_line[0] == "A_Planetary":
                    dkey = "daily_Ap"
                else:
                    dkey = split_line[0]

                data_vals['ap'][dkey] = [int(val) for val in split_line[1:]]

        # Process the Kp data
        hr_strs = ['00-03UT', '03-06UT', '06-09UT', '09-12UT', '12-15UT',
                   '15-18UT', '18-21UT', '21-00UT']
        data_times['kp'] = pds.date_range(pred_times[0], periods=24, freq='3H')

        for line in kp_raw.split('\n'):
            if line.find("Prob_Mid") >= 0:
                break
            elif line.find("UT") > 0:
                split_line = line.split()
                reg, hr = split_line[0].split('/')
                dkey = '{:s}_lat_Kp'.format(reg)

                # Initalize the Kp data for this region
                if dkey not in data_vals['kp'].keys():
                    data_vals['kp'][dkey] = np.full(shape=(24,),
                                                    fill_value=np.nan)

                # Save the Kp data into the correct day and hour index
                hr_index = hr_strs.index(hr)
                data_vals['kp'][dkey][hr_index] = float(split_line[1])
                data_vals['kp'][dkey][hr_index + 8] = float(split_line[2])
                data_vals['kp'][dkey][hr_index + 16] = float(split_line[3])

        # Process the storm probabilities
        for line in storm_raw.split('\n'):
            if line.find("Polar_cap") >= 0:
                break
            elif len(line) > 0:
                split_line = line.split()
                if split_line[0].find('/') > 0:
                    dkey = split_line[0].replace('/', '-Lat_')
                    data_vals['stormprob'][dkey] = [
                        int(val) for val in split_line[1:]]

        # Process the polar cap prediction
        data_vals['polarcap']['absorption_forecast'] = [
            str_val for str_val in pc_raw.split('\n')[1].split()]
        data_times['polarcap'] = [
            ptimes for i, ptimes in enumerate(pred_times)
            if i < len(data_vals['polarcap']['absorption_forecast'])]

        # Process the F10.7 data
        data_vals['f107']['f107'] = [
            int(val) for val in f107_raw.split('\n')[1].split()]

        # Process the flare data
        dkey_root = 'Whole_Disk_Flare_Prob'
        for line in flare_raw.split('\n'):
            if len(line) > 0 and line.find("#") < 0:
                if line.find(":") == 0:
                    dkey_root = line.split(":")[1]
                else:
                    split_line = line.split()

                    if len(split_line) == 4:
                        dkey = "_".join([dkey_root, split_line[0]])
                        data_vals['flare'][dkey] = [
                            int(val) for val in split_line[1:]]
                    else:
                        data_vals['flare']['{:s}_Region'.format(dkey_root)] = [
                            int(split_line[0]), -1, -1]
                        data_vals['flare']['{:s}_Class_C'.format(dkey_root)] = [
                            int(split_line[1]), -1, -1]
                        data_vals['flare']['{:s}_Class_M'.format(dkey_root)] = [
                            int(split_line[2]), -1, -1]
                        data_vals['flare']['{:s}_Class_X'.format(dkey_root)] = [
                            int(split_line[3]), -1, -1]
                        data_vals['flare']['{:s}_Class_P'.format(dkey_root)] = [
                            int(split_line[4]), -1, -1]

        # Save the data by type into files
        for data_name in data_vals.keys():
            # Put the data values into a nicer DataFrame
            data = pds.DataFrame(data_vals[data_name],
                                 index=data_times[data_name])

            # Save the data as a CSV file
            data_tag = 'forecast' if data_name == 'f107' else 'prediction'
            data_file = '_'.join([data_name, data_tag,
                                  '{:s}.txt'.format(dl_date.strftime(
                                      '%Y-%m-%d'))])
            data.to_csv(os.path.join(file_paths[data_name], data_file),
                        header=True)

    return


def geomag_forecast_download(name, date_array, data_path,
                             mock_download_dir=None):
    """Download the 3-day geomagnetic Kp, ap, and storm data from SWPC.

    Parameters
    ----------
    name : str
        Instrument name, expects one of 'kp', 'ap', or 'stormprob'.
    date_array : array-like or pandas.DatetimeIndex
        Array-like or index of datetimes to be downloaded.
    data_path : str
        Path to data directory.
    mock_download_dir : str or NoneType
        Local directory with downloaded files or None. If not None, will
        process any files with the correct name and date as if they were
        downloaded (default=None)

    Raises
    ------
    IOError
        If an unknown mock download directory is supplied or the desired file
        is missing.

    Note
    ----
    Note that the download path for the complementary Instrument will use
    the standard pysat data paths

    """
    pysat.logger.info(forecast_warning)

    # Get the file paths
    file_paths = {data_name: data_path if name == data_name else
                  general.get_instrument_data_path(
                      'sw_{:s}'.format(data_name), tag='forecast')
                  for data_name in ['kp', 'ap', 'stormprob']}

    # Check that the directories exist
    for data_path in file_paths.values():
        pysat.utils.files.check_and_make_path(data_path)

    # Get the file information
    raw_txt = general.get_local_or_remote_text(
        'https://services.swpc.noaa.gov/text/', mock_download_dir,
        '3-day-geomag-forecast.txt')

    if raw_txt is None:
        pysat.logger.info("".join(["Data not downloaded for ",
                                   "3-day-geomag-forecast.txt, data may have ",
                                   "been saved to an unexpected filename."]))
    else:
        # Parse text to get the date the prediction was generated
        date_str = raw_txt.split(':Issued: ')[-1].split(' UTC')[0]
        dl_date = dt.datetime.strptime(date_str, '%Y %b %d %H%M')

        # Separate out the data by chunks
        ap_raw = raw_txt.split('NOAA Ap Index Forecast')[-1]
        kp_raw = raw_txt.split('NOAA Kp index forecast ')[-1]
        storm_raw = raw_txt.split('NOAA Geomagnetic Activity Probabilities')[-1]

        # Get dates of the forecasts
        date_str = kp_raw[0:6] + ' ' + str(dl_date.year)
        forecast_date = dt.datetime.strptime(date_str, '%d %b %Y')

        # Strings we will use to parse the downloaded text for Kp
        lines = ['00-03UT', '03-06UT', '06-09UT', '09-12UT', '12-15UT',
                 '15-18UT', '18-21UT', '21-00UT']

        # Storage for daily Kp forecasts. Get values for each day, then combine
        # them together
        kp_day1 = []
        kp_day2 = []
        kp_day3 = []
        for line in lines:
            raw = kp_raw.split(line)[-1].split('\n')[0]
            cols = raw.split()
            kp_day1.append(float(cols[-3]))
            kp_day2.append(float(cols[-2]))
            kp_day3.append(float(cols[-1]))

        kp_times = pds.date_range(forecast_date, periods=24, freq='3H')
        kp_day = []
        for dd in [kp_day1, kp_day2, kp_day3]:
            kp_day.extend(dd)

        # Put Kp data into nicer DataFrame
        data_frames = {'kp': pds.DataFrame(kp_day, index=kp_times,
                                           columns=['Kp'])}

        # Parse the Ap data
        ap_times = pds.date_range(dl_date - dt.timedelta(days=1), periods=5,
                                  freq='1D')
        obs_line = ap_raw.split('Observed Ap')[-1].split('\n')[0]
        est_line = ap_raw.split('Estimated Ap')[-1].split('\n')[0]
        pred_line = ap_raw.split('Predicted Ap')[-1].split('\n')[0]
        ap_vals = [int(obs_line[-3:]), int(est_line[-3:])]

        for ap_val in pred_line.split()[-1].split('-'):
            ap_vals.append(int(ap_val))

        # Put the Ap data into a nicer DataFrame
        data_frames['ap'] = pds.DataFrame(ap_vals, index=ap_times,
                                          columns=['daily_Ap'])

        # Parse the storm probabilities
        storm_dict = {}
        for storm_line in storm_raw.split('\n')[1:5]:
            storm_split = storm_line.split()

            # Build the storm data column name
            dkey = '_'.join(storm_split[:-1])

            # Assign the storm probabilities
            storm_dict[dkey] = [int(sp) for sp in storm_split[-1].split('/')]

        # Put the storm probabilities into a nicer DataFrame
        storm_times = pds.date_range(forecast_date, periods=3, freq='1D')
        data_frames['stormprob'] = pds.DataFrame(storm_dict, index=storm_times)

        # Save the data files
        for data_name in data_frames.keys():
            filename = '{:s}_forecast_{:s}.txt'.format(
                data_name, dl_date.strftime('%Y-%m-%d'))
            data_frames[data_name].to_csv(os.path.join(
                file_paths[data_name], filename), header=True)

    return


def kp_ap_recent_download(name, date_array, data_path, mock_download_dir=None):
    """Download recent Kp and ap data from SWPC.

    Parameters
    ----------
    name : str
        Instrument name, expects 'kp' or 'ap'.
    date_array : array-like or pandas.DatetimeIndex
        Array-like or index of datetimes to be downloaded.
    data_path : str
        Path to data directory.
    mock_download_dir : str or NoneType
        Local directory with downloaded files or None. If not None, will
        process any files with the correct name and date as if they were
        downloaded (default=None)

    Raises
    ------
    IOError
        If an unknown mock download directory is supplied or the desired file
        is missing.

    Note
    ----
    Note that the download path for the complementary Instrument will use
    the standard pysat data paths

    """
    pysat.logger.info(forecast_warning)

    # Get the file paths
    file_paths = {data_name: data_path if name == data_name else
                  general.get_instrument_data_path(
                      'sw_{:s}'.format(data_name), tag='recent')
                  for data_name in ['kp', 'ap']}

    # Check that the directories exist
    for data_path in file_paths.values():
        pysat.utils.files.check_and_make_path(data_path)

    # Get the file information
    raw_txt = general.get_local_or_remote_text(
        'https://services.swpc.noaa.gov/text/', mock_download_dir,
        'daily-geomagnetic-indices.txt')

    if raw_txt is None:
        pysat.logger.info("".join(["Data not downloaded for ",
                                   "daily-geomagnetic-indices.txt, data may ",
                                   "have been saved to an unexpected ",
                                   "filename."]))
    else:
        # Parse text to get the date the prediction was generated
        date_str = raw_txt.split(':Issued: ')[-1].split('\n')[0]
        dl_date = dt.datetime.strptime(date_str, '%H%M UT %d %b %Y')

        # Data is the forecast value for the next three days
        raw_data = raw_txt.split('#  Date ')[-1]

        # Keep only the middle bits that matter
        raw_data = raw_data.split('\n')[1:-1]

        # Hold times from the file
        times = []

        # Holds Kp and Ap values for each station
        sub_kps = [[], [], []]
        sub_aps = [[], [], []]

        # Iterate through file lines and parse out the info we want
        for line in raw_data:
            times.append(dt.datetime.strptime(line[0:10], '%Y %m %d'))

            # Pick out Kp values for each of the three columns. The columns
            # used to all have integer values, but now some have floats.
            kp_sub_lines = [line[17:33], line[40:56], line[63:]]
            ap_sub_lines = [line[10:17], line[33:40], line[56:63]]
            for i, sub_line in enumerate(kp_sub_lines):
                # Process the Kp data, which has 3-hour values
                split_sub = sub_line.split()
                for ihr in np.arange(8):
                    if sub_line.find('.') < 0:
                        # These are integer values
                        sub_kps[i].append(
                            int(sub_line[(ihr * 2):((ihr + 1) * 2)]))
                    else:
                        # These are float values
                        sub_kps[i].append(np.float64(split_sub[ihr]))

                # Process the Ap data, which has daily values
                sub_aps[i].append(np.int64(ap_sub_lines[i]))

        # Create times on 3 hour cadence
        kp_times = pds.date_range(times[0], periods=(8 * 30), freq='3H')

        # Put both data sets into DataFrames
        data = {'kp': pds.DataFrame({'mid_lat_Kp': sub_kps[0],
                                     'high_lat_Kp': sub_kps[1],
                                     'Kp': sub_kps[2]}, index=kp_times),
                'ap': pds.DataFrame({'mid_lat_Ap': sub_aps[0],
                                     'high_lat_Ap': sub_aps[1],
                                     'daily_Ap': sub_aps[2]}, index=times)}

        # Write out the data sets as files
        for dkey in data.keys():
            data_file = '{:s}_recent_{:s}.txt'.format(
                dkey, dl_date.strftime('%Y-%m-%d'))

            data[dkey].to_csv(os.path.join(file_paths[dkey], data_file),
                              header=True)

    return


def recent_ap_f107_download(name, date_array, data_path,
                            mock_download_dir=None):
    """Download 45-day ap and F10.7 data from SWPC.

    Parameters
    ----------
    name : str
        Instrument name, expects 'f107' or 'ap'.
    date_array : array-like or pandas.DatetimeIndex
        Array-like or index of datetimes to be downloaded.
    data_path : str
        Path to data directory.
    mock_download_dir : str or NoneType
        Local directory with downloaded files or None. If not None, will
        process any files with the correct name and date as if they were
        downloaded (default=None)

    Raises
    ------
    IOError
        If an unknown mock download directory is supplied or the desored file
        is missing.

    Note
    ----
    Note that the download path for the complementary Instrument will use
    the standard pysat data paths

    """
    pysat.logger.info(forecast_warning)

    # Get the file paths
    file_paths = {data_name: data_path if name == data_name else
                  general.get_instrument_data_path(
                      'sw_{:s}'.format(data_name), tag='45day')
                  for data_name in ['f107', 'ap']}

    # Check that the directories exist
    for data_path in file_paths.values():
        pysat.utils.files.check_and_make_path(data_path)

    # Get the file information
    raw_txt = general.get_local_or_remote_text(
        'https://services.swpc.noaa.gov/text/', mock_download_dir,
        '45-day-ap-forecast.txt')

    if raw_txt is None:
        pysat.logger.info("".join(["Data not downloaded for ",
                                   "45-day-ap-forecast.txt, data may have been",
                                   " saved to an unexpected filename."]))
    else:
        # Parse text to get the date the prediction was generated
        date_str = raw_txt.split(':Issued: ')[-1].split(' UTC')[0]
        dl_date = dt.datetime.strptime(date_str, '%Y %b %d %H%M')

        # Get to the forecast data
        raw_data = raw_txt.split('45-DAY AP FORECAST')[-1]

        # Grab Ap part
        raw_ap = raw_data.split('45-DAY F10.7 CM FLUX FORECAST')[0]
        raw_ap = raw_ap.split('\n')[1:-1]

        # Get the F107
        raw_f107 = raw_data.split('45-DAY F10.7 CM FLUX FORECAST')[-1]
        raw_f107 = raw_f107.split('\n')[1:-4]

        # Parse the data
        ap_times, ap = parse_45day_block(raw_ap)
        f107_times, f107 = parse_45day_block(raw_f107)

        # Save the data in DataFrames
        data = {'ap': pds.DataFrame(ap, index=ap_times, columns=['daily_Ap']),
                'f107': pds.DataFrame(f107, index=f107_times, columns=['f107'])}

        # Write out the data files
        for data_name in data.keys():
            file_name = '{:s}_45day_{:s}.txt'.format(
                data_name, dl_date.strftime('%Y-%m-%d'))
            data[data_name].to_csv(os.path.join(file_paths[data_name],
                                                file_name), header=True)

    return


def parse_45day_block(block_lines):
    """Parse the data blocks used in the 45-day Ap and F10.7 Flux Forecast file.

    Parameters
    ----------
    block_lines : list
        List of lines containing data in this data block

    Returns
    -------
    dates : list
        List of dates for each date/data pair in this block
    values : list
        List of values for each date/data pair in this block

    """

    # Initialize the output
    dates = list()
    values = list()

    # Cycle through each line in this block
    for line in block_lines:
        # Split the line on whitespace
        split_line = line.split()

        # Format the dates
        dates.extend([dt.datetime.strptime(tt, "%d%b%y")
                      for tt in split_line[::2]])

        # Format the data values
        values.extend([int(vv) for vv in split_line[1::2]])

    return dates, values


def list_files(name, tag, inst_id, data_path, format_str=None):
    """List local files for Kp or ap data obtained from SWPC.

    Parameters
    ----------
    name : str
        Instrument name.
    tag : str
        String specifying the database, expects 'def' (definitive) or 'now'
        (nowcast)
    inst_id : str
        Specifies the instrument identification, not used.
    data_path : str
        Path to data directory.
    format_str : str or NoneType
        User specified file format.  If None is specified, the default
        formats associated with the supplied tags are used. (default=None)

    Returns
    -------
    files : pysat._files.Files
        A class containing the verified available files

    """

    if format_str is None:
        format_str = '_'.join([name, tag,
                               '{year:04d}-{month:02d}-{day:02d}.txt'])
    files = pysat.Files.from_os(data_path=data_path, format_str=format_str)

    # Pad list of files data to include most recent file under tomorrow
    if not files.empty:
        pds_offset = dt.timedelta(days=1)
        files.loc[files.index[-1] + pds_offset] = files.values[-1]
        files.loc[files.index[-1] + pds_offset] = files.values[-1]

    return files
