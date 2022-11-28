#!/usr/bin/env python
# -*- coding: utf-8 -*-.
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
# ----------------------------------------------------------------------------
"""Provides routines that support SWPC space weather instruments."""

import datetime as dt
import numpy as np
import os
import pandas as pds
import requests

import pysat

from pysatSpaceWeather.instruments.methods import general
from pysatSpaceWeather.instruments.methods import f107 as mm_f107

# ----------------------------------------------------------------------------
# Define the module variables

ackn = ''.join(['Prepared by the U.S. Dept. of Commerce, NOAA, Space ',
                'Weather Prediction Center'])
forecast_warning = ''.join(['This routine can only download the current ',
                            'forecast, not archived forecasts'])


# ----------------------------------------------------------------------------
# Define the module functions

def solar_geomag_predictions_download(name, date_array, data_path):
    """Download the 3-day solar-geomagnetic predictions from SWPC.

    Parameters
    ----------
    name : str
        Instrument name, expects one of 'kp', 'ap', 'storm-prob', 'f107',
        'flare', or 'polar-cap'.
    date_array : array-like or pandas.DatetimeIndex
        Array-like or index of datetimes to be downloaded.
    data_path : str
        Path to data directory.

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
                  for data_name in ['kp', 'ap', 'storm-prob', 'f107', 'flare',
                                    'polar-cap']}

    # Download webpage
    furl = ''.join(['https://services.swpc.noaa.gov/text/',
                    '3-day-solar-geomag-predictions.txt'])
    req = requests.get(furl)

    # Parse text to get the date the prediction was generated
    date_str = req.text.split(':Issued: ')[-1].split(' UTC')[0]
    dl_date = dt.datetime.strptime(date_str, '%Y %b %d %H%M')

    # Parse the data to get the prediction dates
    date_strs = req.text.split(':Prediction_dates:')[-1].split('\n')[0]
    pred_times = [dt.datetime.strptime(' '.join(date_str.split()), '%Y %b %d')
                  for date_str in date_strs.split('  ') if len(date_str) > 0]

    # Separate out the data by chunks
    ap_raw = req.text.split(':Geomagnetic_A_indices:')[-1]
    kp_raw = req.text.split(':Pred_Mid_k:')[-1]
    storm_raw = req.text.split(':Prob_Mid:')[-1]
    pc_raw = req.text.split(':Polar_cap:')[-1]
    f107_raw = req.text.split(':10cm_flux:')[-1]
    flare_raw = req.text.split(':Whole_Disk_Flare_Prob:')[-1]

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
    hr_strs = ['00-03UT', '03-06UT', '06-09UT', '09-12UT', '12-15UT', '15-18UT',
               '18-21UT', '21-00UT']
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
                data_vals['kp'][dkey] = np.full(shape=(24,), fill_value=np.nan)

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
                data_vals['storm-prob'][dkey] = [
                    int(val) for val in split_line[1:]]

    # Process the polar cap prediction
    data_vals['polar-cap']['absorption_forecast'] = [
        str_val for str_val in pc_raw.split('\n')[1].split()]
    data_times['polar-cap'] = [
        ptimes for i, ptimes in enumerate(pred_times)
        if i < len(data_vals['polar-cap']['absorption_forecast'])]

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
        data = pds.DataFrame(data_vals[data_name], index=data_times[data_name])

        # Save the data as a CSV file
        data_file = '_'.join([data_name, 'prediction',
                              '{:s}.txt'.format(dl_date.strftime('%Y-%m-%d'))])
        data.to_csv(os.path.join(file_paths[data_name], data_file), header=True)

    return


def geomag_forecast_download(name, date_array, data_path):
    """Download the 3-day geomagnetic Kp, ap, and storm data from SWPC.

    Parameters
    ----------
    name : str
        Instrument name, expects one of 'kp', 'ap', or 'storm-prob'.
    date_array : array-like or pandas.DatetimeIndex
        Array-like or index of datetimes to be downloaded.
    data_path : str
        Path to data directory.

    Note
    ----
    Note that the download path for the complementary Instrument will use
    the standard pysat data paths

    """
    pysat.logger.info(forecast_warning)

    # Get the file paths
    if name == 'kp':
        kp_path = data_path
        ap_path = general.get_instrument_data_path('sw_ap', tag='forecast')
        storm_path = general.get_instrument_data_path('sw_storm-prob',
                                                      tag='forecast')
    elif name == 'ap':
        ap_path = data_path
        kp_path = general.get_instrument_data_path('sw_kp', tag='forecast')
        storm_path = general.get_instrument_data_path('sw_storm-prob',
                                                      tag='forecast')
    else:
        storm_path = data_path
        ap_path = general.get_instrument_data_path('sw_ap', tag='forecast')
        kp_path = general.get_instrument_data_path('sw_kp', tag='forecast')

    # Download webpage
    furl = 'https://services.swpc.noaa.gov/text/3-day-geomag-forecast.txt'
    req = requests.get(furl)

    # Parse text to get the date the prediction was generated
    date_str = req.text.split(':Issued: ')[-1].split(' UTC')[0]
    dl_date = dt.datetime.strptime(date_str, '%Y %b %d %H%M')

    # Separate out the data by chunks
    ap_raw = req.text.split('NOAA Ap Index Forecast')[-1]
    kp_raw = req.text.split('NOAA Kp index forecast ')[-1]
    storm_raw = req.text.split('NOAA Geomagnetic Activity Probabilities')[-1]

    # Get dates of the forecasts
    date_str = kp_raw[0:6] + ' ' + str(dl_date.year)
    forecast_date = dt.datetime.strptime(date_str, '%d %b %Y')

    # Strings we will use to parse the downloaded text for Kp
    lines = ['00-03UT', '03-06UT', '06-09UT', '09-12UT', '12-15UT', '15-18UT',
             '18-21UT', '21-00UT']

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
    kp_data = pds.DataFrame(kp_day, index=kp_times, columns=['Kp'])

    # Save the Kp data
    kp_file = 'kp_forecast_{:s}.txt'.format(dl_date.strftime('%Y-%m-%d'))
    kp_data.to_csv(os.path.join(kp_path, kp_file), header=True)

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
    ap_data = pds.DataFrame(ap_vals, index=ap_times, columns=['daily_Ap'])

    # Save the Ap data
    ap_file = 'ap_forecast_{:s}.txt'.format(dl_date.strftime('%Y-%m-%d'))
    ap_data.to_csv(os.path.join(ap_path, ap_file), header=True)

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
    storm_data = pds.DataFrame(storm_dict, index=storm_times)

    # Save the storm probabilities
    storm_file = 'storm-prob_forecast_{:s}.txt'.format(dl_date.strftime(
        '%Y-%m-%d'))
    storm_data.to_csv(os.path.join(storm_path, storm_file), header=True)

    return


def kp_ap_recent_download(name, date_array, data_path):
    """Download recent Kp and ap data from SWPC.

    Parameters
    ----------
    name : str
        Instrument name, expects 'kp' or 'ap'.
    date_array : array-like or pandas.DatetimeIndex
        Array-like or index of datetimes to be downloaded.
    data_path : str
        Path to data directory.

    Note
    ----
    Note that the download path for the complementary Instrument will use
    the standard pysat data paths

    """
    pysat.logger.info(forecast_warning)

    # Download webpage
    rurl = ''.join(('https://services.swpc.noaa.gov/text/',
                    'daily-geomagnetic-indices.txt'))
    req = requests.get(rurl)

    # Parse text to get the date the prediction was generated
    date_str = req.text.split(':Issued: ')[-1].split('\n')[0]
    dl_date = dt.datetime.strptime(date_str, '%H%M UT %d %b %Y')

    # Data is the forecast value for the next three days
    raw_data = req.text.split('#  Date ')[-1]

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
                    sub_kps[i].append(float(split_sub[ihr]))

            # Process the Ap data, which has daily values
            sub_aps[i].append(int(ap_sub_lines[i]))

    # Create times on 3 hour cadence
    kp_times = pds.date_range(times[0], periods=(8 * 30), freq='3H')

    # Put Kp data into DataFrame
    data = pds.DataFrame({'mid_lat_Kp': sub_kps[0], 'high_lat_Kp': sub_kps[1],
                          'Kp': sub_kps[2]}, index=kp_times)

    # Write Kp out as a file
    data_file = 'kp_recent_{:s}.txt'.format(dl_date.strftime('%Y-%m-%d'))

    if name == 'kp':
        kp_path = data_path
    else:
        kp_path = general.get_instrument_data_path('sw_kp', tag='recent')

    data.to_csv(os.path.join(kp_path, data_file), header=True)

    # Put Ap data into a DataFrame
    data = pds.DataFrame({'mid_lat_Ap': sub_aps[0], 'high_lat_Ap': sub_aps[1],
                          'daily_Ap': sub_kps[2]}, index=times)

    # Write Kp out as a file
    data_file = 'ap_recent_{:s}.txt'.format(dl_date.strftime('%Y-%m-%d'))

    if name == 'ap':
        ap_path = data_path
    else:
        ap_path = general.get_instrument_data_path('sw_ap', tag='recent')

    data.to_csv(os.path.join(ap_path, data_file), header=True)

    return


def recent_ap_f107_download(name, date_array, data_path):
    """Download 45-day ap and F10.7 data from SWPC.

    Parameters
    ----------
    name : str
        Instrument name, expects 'f107' or 'ap'.
    date_array : array-like or pandas.DatetimeIndex
        Array-like or index of datetimes to be downloaded.
    data_path : str
        Path to data directory.

    Note
    ----
    Note that the download path for the complementary Instrument will use
    the standard pysat data paths

    """
    pysat.logger.info(forecast_warning)

    # Set the download webpage
    furl = 'https://services.swpc.noaa.gov/text/45-day-ap-forecast.txt'
    req = requests.get(furl)

    # Parse text to get the date the prediction was generated
    date_str = req.text.split(':Issued: ')[-1].split(' UTC')[0]
    dl_date = dt.datetime.strptime(date_str, '%Y %b %d %H%M')

    # Get to the forecast data
    raw_data = req.text.split('45-DAY AP FORECAST')[-1]

    # Grab Ap part
    raw_ap = raw_data.split('45-DAY F10.7 CM FLUX FORECAST')[0]
    raw_ap = raw_ap.split('\n')[1:-1]

    # Get the F107
    raw_f107 = raw_data.split('45-DAY F10.7 CM FLUX FORECAST')[-1]
    raw_f107 = raw_f107.split('\n')[1:-4]

    # Parse the Ap data
    ap_times, ap = mm_f107.parse_45day_block(raw_ap)
    ap_data = pds.DataFrame(ap, index=ap_times, columns=['daily_Ap'])

    # Parse the F10.7 data
    f107_times, f107 = mm_f107.parse_45day_block(raw_f107)
    f107_data = pds.DataFrame(f107, index=f107_times, columns=['f107'])

    # Get the data directories
    if name == 'ap':
        ap_path = data_path
        f107_path = general.get_instrument_data_path('sw_f107', tag='45day')
    else:
        ap_path = general.get_instrument_data_path('sw_ap', tag='45day')
        f107_path = data_path

    # Write out the Ap data file
    ap_file = 'ap_45day_{:s}.txt'.format(dl_date.strftime('%Y-%m-%d'))
    ap_data.to_csv(os.path.join(ap_path, ap_file), header=True)

    # Write out the F107 data file
    f107_file = 'f107_45day_{:s}.txt'.format(dl_date.strftime('%Y-%m-%d'))
    f107_data.to_csv(os.path.join(f107_path, f107_file), header=True)

    return


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
        pds_offset = pds.DateOffset(days=1)
        files.loc[files.index[-1] + pds_offset] = files.values[-1]
        files.loc[files.index[-1] + pds_offset] = files.values[-1]

    return files
