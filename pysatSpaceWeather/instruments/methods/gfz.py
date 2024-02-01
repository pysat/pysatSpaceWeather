#!/usr/bin/env python
# -*- coding: utf-8 -*-.
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
#
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
"""Provides routines that support GFZ space weather instruments."""

import datetime as dt
import json
import numpy as np
import os
import pandas as pds
import requests

import pysat

from pysatSpaceWeather.instruments.methods import general

# ----------------------------------------------------------------------------
# Define the module variables

ackn = ''.join(['CC BY 4.0, This index is produced by the Geomagnetic ',
                'Observatory Niemegk, GFZ German Research Centre for ',
                'Geosciences.  Please cite the references in the ',
                "'references' attribute"])
geoind_refs = '\n'.join([''.join(["Bartels, J. (1949) - The standardized index",
                                  "Ks and the planetary index Kp, IATME ",
                                  "Bulletin 12b, 97."]),
                         ''.join(["Matzka, J., Bronkalla, O., Tornow, K., ",
                                  "Elger, K. and Stolle, C., 2021. ",
                                  "Geomagnetic Kp index. V. 1.0. GFZ Data ",
                                  "Services, doi:10.5880/Kp.0001"]),
                         ''.join(["Matzka, J., Stolle, C., Yamazaki, Y., ",
                                  "Bronkalla, O. and Morschhauser, A., 2021. ",
                                  "The geomagnetic Kp index and derived ",
                                  "indices of geomagnetic activity. Space ",
                                  "Weather,doi:10.1029/2020SW002641"])])
hpo_refs = '\n'.join([''.join(["Yamazaki, Y., Matzka, J., Stolle, C., ",
                               "Kervalishvili, G., Rauberg, J., Bronkalla, O.,",
                               " Morschhauser, A., Bruinsma, S., Shprits, ",
                               "Y.Y., Jackson, D.R., 2022. Geomagnetic ",
                               "Activity Index Hpo. Geophys. Res. Lett., 49, ",
                               "e2022GL098860, doi:10.1029/2022GL098860"]),
                      ''.join(["Matzka, J., Bronkalla, O., Kervalishvili, G.,",
                               " Rauberg, J. and Yamazaki, Y., 2022. ",
                               "Geomagnetic Hpo index. V. 2.0. GFZ Data ",
                               "Services, doi:10.5880/Hpo.0002"])])


# ----------------------------------------------------------------------------
# Define the module functions

def json_downloads(date_array, data_path, local_file_prefix, local_date_fmt,
                   gfz_data_name, freq, update_files=False, is_def=False,
                   mock_download_dir=None):
    """Download data from GFZ into CSV files at a specified cadence.

    Parameters
    ----------
    date_array : array-like or pandas.DatetimeIndex
        Array-like or index of datetimes to be downloaded.
    data_path : str
        Path to data directory.
    local_file_prefix : str
        Prefix for local files, e.g., 'tag_' or 'tag_monthly_'
    local_date_fmt : str
        String format for the local filename, e.g., '%Y-%m-%d' or '%Y-%m'
    gfz_data_name : str
        Name of the data index on the GFZ server, expects one of: 'Kp', 'ap',
        'Ap', 'Cp', 'C9', 'Hp30', 'Hp60', 'ap30', 'ap60', 'SN', 'Fobs', 'Fadj'
        where SN is the international sunspot number and Fxxx is the observed
        and adjusted F10.7.
    freq : pds.DateOffset or dt.timedelta
        Offset to add to the start date to ensure all data is downloaded
        (inclusive)
    update_files : bool
        Re-download data for files that already exist if True (default=False)
    is_def : bool
        If true, selects only the definitive data, otherwise also includes
        nowcast data (default=False)
    mock_download_dir : str or NoneType
        Local directory with downloaded files or None. If not None, will
        process any files with the correct name and date (following the local
        file prefix and date format) as if they were downloaded (default=None)

    Raises
    ------
    IOError
        If there is a gateway timeout when downloading data or if an unknown
        mock download directory is supplied.

    """

    # If a mock download directory was supplied, test to see it exists
    if mock_download_dir is not None:
        if not os.path.isdir(mock_download_dir):
            raise IOError('file location is not a directory: {:}'.format(
                mock_download_dir))

    # Set the local variables
    base_url = "https://kp.gfz-potsdam.de/app/json/"
    time_fmt = "%Y-%m-%dT%H:%M:%SZ"
    last_file = ''

    # Cycle through all the dates
    for dl_date in date_array:
        # Build the local filename
        local_fname = ''.join([local_file_prefix,
                               dl_date.strftime(local_date_fmt), '.txt'])
        local_file = os.path.join(data_path, local_fname)

        # Determine if the download should occur
        if not os.path.isfile(local_file) or (update_files
                                              and local_file != last_file):
            if mock_download_dir is None:
                # Get the URL for the desired data
                stop = dl_date + freq
                query_url = "{:s}?start={:s}&end={:s}&index={:s}".format(
                    base_url, dl_date.strftime(time_fmt),
                    stop.strftime(time_fmt), gfz_data_name)

                if is_def:
                    # Add the definitive flag
                    query_url = '{:s}&status=def'.format(query_url)

                # The data is returned as a JSON file
                req = requests.get(query_url)

                # Process the JSON file
                if req.text.find('Gateway Timeout') >= 0:
                    raise IOError(''.join(['Gateway timeout when requesting ',
                                           'file using command: ', query_url]))

                raw_txt = req.text if req.ok else None
            else:
                # Get the text from the downloaded file
                query_url = os.path.join(mock_download_dir, local_fname)
                if os.path.isfile(query_url):
                    with open(query_url, 'r') as fpin:
                        raw_txt = fpin.read()
                else:
                    raw_txt = None

            if raw_txt is not None:
                raw_dict = json.loads(raw_txt)
                data = pds.DataFrame.from_dict({gfz_data_name:
                                                raw_dict[gfz_data_name]})
                if data.empty:
                    pysat.logger.warning("no data for {:}".format(dl_date))
                else:
                    # Convert the datetime strings to datetime objects
                    time_list = [dt.datetime.strptime(time_str, time_fmt)
                                 for time_str in raw_dict['datetime']]

                    # Add the time index
                    data.index = time_list

                    # Create a local CSV file
                    data.to_csv(local_file, header=True)
            else:
                pysat.logger.info("".join(["Data not downloaded for ",
                                           dl_date.strftime("%d %b %Y"),
                                           ", date may be out of range ",
                                           "for the database or data may ",
                                           "have been saved to an unexpected",
                                           " filename: {:}".format(query_url)]))
    return


def kp_ap_cp_download(platform, name, date_array, tag, inst_id, data_path,
                      mock_download_dir=None):
    """Download Kp, ap, and Cp data from GFZ.

    Parameters
    ----------
    platform : str
        Instrument platform.
    name : str
        Instrument name.
    date_array : array-like or pandas.DatetimeIndex
        Array-like or index of datetimes to be downloaded.
    tag : str
        String specifying the database, expects 'def' (definitive) or 'now'
        (nowcast)
    inst_id : str
        Specifies the instrument identification, not used.
    data_path : str
        Path to data directory.
    mock_download_dir : str or NoneType
        Local directory with downloaded files or None. If not None, will
        process any files with the correct name and date (following the local
        file prefix and date format) as if they were downloaded (default=None)

    Raises
    ------
    ValueError
        If an unknown instrument module is supplied.
    IOError
        If an unknown mock download directory is supplied.

    Note
    ----
    Note that the download path for the complementary Instrument will use
    the standard pysat data paths

    """
    # If a mock download directory was supplied, test to see it exists
    if mock_download_dir is not None:
        if not os.path.isdir(mock_download_dir):
            raise IOError('file location is not a directory: {:}'.format(
                mock_download_dir))

    # Set the page for the definitive or nowcast Kp
    burl = ''.join(['https://datapub.gfz-potsdam.de/download/10.5880.Kp.0001',
                    '/Kp_', 'nowcast' if tag == 'now' else 'definitive', '/'])
    data_cols = ['Bartels_solar_rotation_num', 'day_within_Bartels_rotation',
                 'Kp', 'daily_Kp_sum', 'ap', 'daily_Ap', 'Cp', 'C9']
    hours = np.arange(0, 24, 3)
    kp_translate = {'0': 0.0, '3': 1.0 / 3.0, '7': 2.0 / 3.0}
    dnames = list()

    inst_cols = {'sw_kp': [0, 1, 2, 3], 'sw_cp': [0, 1, 6, 7],
                 'sw_ap': [0, 1, 4, 5]}

    # Construct the Instrument module name from the platform and name
    inst_mod_name = '_'.join([platform, name])
    if inst_mod_name not in inst_cols.keys():
        raise ValueError('Unknown Instrument module {:}, expected {:}'.format(
            inst_mod_name, inst_cols.keys()))

    data_paths = {inst_mod: data_path if inst_mod == inst_mod_name else
                  general.get_instrument_data_path(inst_mod, tag=tag,
                                                   inst_id=inst_id)
                  for inst_mod in inst_cols.keys()}

    # Check that the directories exist
    for data_path in data_paths.values():
        pysat.utils.files.check_and_make_path(data_path)

    # Cycle through all the times
    for dl_date in date_array:
        fname = 'Kp_{:s}{:04d}.wdc'.format(tag, dl_date.year)
        if fname not in dnames:
            pysat.logger.info(' '.join(('Downloading file for',
                                        dl_date.strftime('%Y'))))
            if mock_download_dir is None:
                furl = ''.join([burl, fname])
                req = requests.get(furl)

                raw_txt = req.text if req.ok else None
            else:
                furl = os.path.join(mock_download_dir, fname)
                if os.path.isfile(furl):
                    with open(furl, "r") as fpin:
                        raw_txt = fpin.read()
                else:
                    raw_txt = None

            if raw_txt is not None:
                # Split the file text into lines
                lines = raw_txt.split('\n')[:-1]

                # Remove the header
                while lines[0].find('#') == 0:
                    lines.pop(0)

                # Process the data lines
                ddict = {dkey: list() for dkey in data_cols}
                times = list()
                for line in lines:
                    ldate = dt.datetime.strptime(' '.join([
                        "{:02d}".format(int(dd)) for dd in
                        [line[:2], line[2:4], line[4:6]]]), "%y %m %d")
                    bsr_num = int(line[6:10])
                    bsr_day = int(line[10:12])
                    if line[28:30] == '  ':
                        kp_ones = 0.0
                    else:
                        kp_ones = float(line[28:30])
                    sum_kp = kp_ones + kp_translate[line[30]]
                    daily_ap = int(line[55:58])
                    cp = float(line[58:61])
                    c9 = int(line[61])

                    for i, hour in enumerate(hours):
                        # Set the time for this hour and day
                        times.append(ldate + dt.timedelta(hours=int(hour)))

                        # Set the daily values for this hour
                        ddict['Bartels_solar_rotation_num'].append(bsr_num)
                        ddict['day_within_Bartels_rotation'].append(bsr_day)
                        ddict['daily_Kp_sum'].append(sum_kp)
                        ddict['daily_Ap'].append(daily_ap)
                        ddict['Cp'].append(cp)
                        ddict['C9'].append(c9)

                        # Get the hourly-specific values
                        ikp = i * 2
                        kp_ones = line[12 + ikp]
                        if kp_ones == ' ':
                            kp_ones = 0.0
                        ddict['Kp'].append(np.float64(kp_ones)
                                           + kp_translate[line[13 + ikp]])
                        iap = i * 3
                        ddict['ap'].append(np.int64(line[31 + iap:34 + iap]))

                # Put data into nicer DataFrames
                for inst_mod in inst_cols.keys():
                    sel_cols = np.array(data_cols)[inst_cols[inst_mod]]
                    sel_dict = {col: ddict[col] for col in sel_cols}
                    data = pds.DataFrame(sel_dict, index=times,
                                         columns=sel_cols)

                    # Write out as a CSV file
                    sfname = fname.replace('Kp',
                                           inst_mod.split('_')[-1].capitalize())
                    saved_fname = os.path.join(data_paths[inst_mod],
                                               sfname).replace('.wdc', '.txt')
                    data.to_csv(saved_fname, header=True)

                # Record the filename so we don't download it twice
                dnames.append(fname)
            else:
                pysat.logger.info("".join(["Unable to download data for ",
                                           dl_date.strftime("%d %b %Y"),
                                           ", date may be out of range for ",
                                           "the database or data may have been",
                                           " saved to an unexpected filename: ",
                                           furl]))
    return


def kp_ap_cp_list_files(name, tag, inst_id, data_path, format_str=None):
    """List local files for Kp, ap, or Cp data obtained from GFZ.

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
        format_str = ''.join(['_'.join([name.capitalize(), tag]),
                              '{year:04d}.txt'])

    # Files are stored by year, going to add a date to the yearly filename for
    # each month and day of month.  The load routine will load the year and use
    # the append date to select out approriate data.
    files = pysat.Files.from_os(data_path=data_path, format_str=format_str)
    if not files.empty:
        files.loc[files.index[-1]
                  + pds.DateOffset(years=1, days=-1)] = files.iloc[-1]
        files = files.asfreq('D', 'pad')
        files = files + '_' + files.index.strftime('%Y-%m-%d')

    return files


def load_def_now(fnames):
    """Load GFZ yearly definitive or nowcast index data.

    Parameters
    ----------
    fnames : pandas.Series
        Series of filenames

    Returns
    -------
    data : pandas.DataFrame
        Object containing satellite data

    """

    # Load the definitive or nowcast data. The GFZ index data are stored in
    # yearly or monthly files that are separated by index ondownload. We need
    # to return data daily. The daily date is attached to filename. Parse off
    # the last date, load all data, and downselect to the desired day
    unique_fnames = dict()
    for filename in fnames:
        fname = filename[0:-11]
        fdate = dt.datetime.strptime(filename[-10:], '%Y-%m-%d')
        if fname not in unique_fnames.keys():
            unique_fnames[fname] = [fdate]
        else:
            unique_fnames[fname].append(fdate)

    # Load the desired filenames
    all_data = []
    for fname in unique_fnames.keys():
        # The daily date is attached to the filename.  Parse off the last
        # date, load the year of data, downselect to the desired day
        fdate = min(unique_fnames[fname])
        temp = pds.read_csv(fname, index_col=0, parse_dates=True)

        if temp.empty:
            pysat.logger.warn('Empty file: {:}'.format(fname))
            continue

        # Select the desired times and add to data list
        all_data.append(pds.DataFrame(temp[fdate:max(unique_fnames[fname])
                                           + dt.timedelta(seconds=86399)]))

    # Combine data together
    if len(all_data) > 0:
        data = pds.concat(all_data, axis=0, sort=True)
    else:
        data = pds.DataFrame()

    return data
