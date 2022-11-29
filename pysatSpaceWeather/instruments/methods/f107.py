#!/usr/bin/env python
# -*- coding: utf-8 -*-.
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
# ----------------------------------------------------------------------------

"""Routines for the F10.7 solar index."""

import datetime as dt
import numpy as np
from packaging.version import Version

import pandas as pds
import pysat

import pysatSpaceWeather as pysat_sw


def acknowledgements(tag):
    """Define the acknowledgements for the F10.7 data.

    Parameters
    ----------
    tag : str
        Tag of the space waether index

    Returns
    -------
    ackn : str
        Acknowledgements string associated with the appropriate F10.7 tag.

    """
    lisird = 'NOAA radio flux obtained through LISIRD'
    swpc = ''.join(['Prepared by the U.S. Dept. of Commerce, NOAA, Space ',
                    'Weather Prediction Center'])

    ackn = {'historic': lisird, 'prelim': swpc, 'daily': swpc,
            'forecast': swpc, '45day': swpc}

    return ackn[tag]


def references(tag):
    """Define the references for the F10.7 data.

    Parameters
    ----------
    tag : str
        Instrument tag for the F10.7 data.

    Returns
    -------
    refs : str
        Reference string associated with the appropriate F10.7 tag.

    """
    noaa_desc = ''.join(['Dataset description: ',
                         'https://www.ngdc.noaa.gov/stp/space-weather/',
                         'solar-data/solar-features/solar-radio/noontime-flux',
                         '/penticton/documentation/dataset-description',
                         '_penticton.pdf, accessed Dec 2020'])
    orig_ref = ''.join(["Covington, A.E. (1948), Solar noise observations on",
                        " 10.7 centimetersSolar noise observations on 10.7 ",
                        "centimeters, Proceedings of the IRE, 36(44), ",
                        "p 454-457."])
    swpc_desc = ''.join(['Dataset description: https://www.swpc.noaa.gov/',
                         'sites/default/files/images/u2/Usr_guide.pdf'])

    refs = {'historic': "\n".join([noaa_desc, orig_ref]),
            'prelim': "\n".join([swpc_desc, orig_ref]),
            'daily': "\n".join([swpc_desc, orig_ref]),
            'forecast': "\n".join([swpc_desc, orig_ref]),
            '45day': "\n".join([swpc_desc, orig_ref])}

    return refs[tag]


def combine_f107(standard_inst, forecast_inst, start=None, stop=None):
    """Combine the output from the measured and forecasted F10.7 sources.

    Parameters
    ----------
    standard_inst : pysat.Instrument or NoneType
        Instrument object containing data for the 'sw' platform, 'f107' name,
        and 'historic', 'prelim', or 'daily' tag
    forecast_inst : pysat.Instrument or NoneType
        Instrument object containing data for the 'sw' platform, 'f107' name,
        and 'prelim', '45day' or 'forecast' tag
    start : dt.datetime or NoneType
        Starting time for combining data, or None to use earliest loaded
        date from the pysat Instruments (default=None)
    stop : dt.datetime or NoneType
        Ending time for combining data, or None to use the latest loaded date
        from the pysat Instruments (default=None)

    Returns
    -------
    f107_inst : pysat.Instrument
        Instrument object containing F10.7 observations for the desired period
        of time, merging the standard, 45day, and forecasted values based on
        their reliability

    Raises
    ------
    ValueError
        If appropriate time data is not supplied, or if the date range is badly
        formed.

    Notes
    -----
    Merging prioritizes the standard data, then the 45day data, and finally
    the forecast data

    Will not attempt to download any missing data, but will load data

    """

    # Initialize metadata and flags
    notes = "Combines data from"
    stag = standard_inst.tag if len(standard_inst.tag) > 0 else 'default'
    tag = 'combined_{:s}_{:s}'.format(stag, forecast_inst.tag)
    inst_flag = 'standard'

    # If the start or stop times are not defined, get them from the Instruments
    if start is None:
        stimes = [inst.index.min() for inst in [standard_inst, forecast_inst]
                  if len(inst.index) > 0]
        start = min(stimes) if len(stimes) > 0 else None

    if stop is None:
        stimes = [inst.index.max() for inst in [standard_inst, forecast_inst]
                  if len(inst.index) > 0]
        stop = max(stimes) + pds.DateOffset(days=1) if len(stimes) > 0 else None

    if start is None or stop is None:
        raise ValueError(' '.join(("must either load in Instrument objects or",
                                   "provide starting and ending times")))

    if start >= stop:
        raise ValueError("date range is zero or negative")

    # Initialize the output instrument
    f107_inst = pysat.Instrument()
    f107_inst.inst_module = pysat_sw.instruments.sw_f107
    f107_inst.tag = tag
    f107_inst.date = start
    f107_inst.doy = np.int64(start.strftime("%j"))
    fill_val = None

    f107_times = list()
    f107_values = list()

    # Cycle through the desired time range
    itime = start

    while itime < stop and inst_flag is not None:
        # Load and save the standard data for as many times as possible
        if inst_flag == 'standard':
            # Test to see if data loading is needed
            if not np.any(standard_inst.index == itime):
                # Set the load kwargs, which vary by pysat version and tag
                load_kwargs = {'date': itime}

                if Version(pysat.__version__) > Version('3.0.1'):
                    load_kwargs['use_header'] = True

                if standard_inst.tag == 'daily':
                    # Add 30 days
                    load_kwargs['date'] += dt.timedelta(days=30)

                standard_inst.load(**load_kwargs)

            good_times = ((standard_inst.index >= itime)
                          & (standard_inst.index < stop))

            if notes.find("standard") < 0:
                notes += " the {:} source ({:} to ".format(inst_flag,
                                                           itime.date())

            if np.any(good_times):
                if fill_val is None:
                    f107_inst.meta = standard_inst.meta
                    fill_val = f107_inst.meta['f107'][
                        f107_inst.meta.labels.fill_val]

                good_vals = standard_inst['f107'][good_times] != fill_val
                new_times = list(standard_inst.index[good_times][good_vals])
                f107_times.extend(new_times)
                new_vals = list(standard_inst['f107'][good_times][good_vals])
                f107_values.extend(new_vals)
                itime = f107_times[-1] + pds.DateOffset(days=1)
            else:
                inst_flag = 'forecast'
                notes += "{:})".format(itime.date())

        # Load and save the forecast data for as many times as possible
        if inst_flag == "forecast":
            # Determine which files should be loaded
            if len(forecast_inst.index) == 0:
                files = np.unique(forecast_inst.files.files[itime:stop])
            else:
                files = [None]  # No load needed, if already initialized

            # Cycle through all possible files of interest, saving relevant
            # data
            for filename in files:
                if filename is not None:
                    load_kwargs = {'fname': filename}
                    if Version(pysat.__version__) > Version('3.0.1'):
                        load_kwargs['use_header'] = True

                    forecast_inst.load(**load_kwargs)

                if notes.find("forecast") < 0:
                    notes += " the {:} source ({:} to ".format(inst_flag,
                                                               itime.date())

                # Check in case there was a problem with the standard data
                if fill_val is None:
                    f107_inst.meta = forecast_inst.meta
                    fill_val = f107_inst.meta['f107'][
                        f107_inst.meta.labels.fill_val]

                # Determine which times to save
                good_times = ((forecast_inst.index >= itime)
                              & (forecast_inst.index < stop))
                good_vals = forecast_inst['f107'][good_times] != fill_val

                # Save desired data and cycle time
                if len(good_vals) > 0:
                    new_times = list(
                        forecast_inst.index[good_times][good_vals])
                    f107_times.extend(new_times)
                    new_vals = list(
                        forecast_inst['f107'][good_times][good_vals])
                    f107_values.extend(new_vals)
                    itime = f107_times[-1] + pds.DateOffset(days=1)

            notes += "{:})".format(itime.date())

            inst_flag = None

    if inst_flag is not None:
        notes += "{:})".format(itime.date())

    # Determine if the beginning or end of the time series needs to be padded
    if len(f107_times) >= 2:
        freq = pysat.utils.time.calc_freq(f107_times)
    else:
        freq = None
    end_date = stop - pds.DateOffset(days=1)
    date_range = pds.date_range(start=start, end=end_date, freq=freq)

    if len(f107_times) == 0:
        f107_times = date_range

    date_range = pds.date_range(start=start, end=end_date, freq=freq)

    if date_range[0] < f107_times[0]:
        # Extend the time and value arrays from their beginning with fill
        # values
        itime = abs(date_range - f107_times[0]).argmin()
        f107_times.reverse()
        f107_values.reverse()
        extend_times = list(date_range[:itime])
        extend_times.reverse()
        f107_times.extend(extend_times)
        f107_values.extend([fill_val for kk in extend_times])
        f107_times.reverse()
        f107_values.reverse()

    if date_range[-1] > f107_times[-1]:
        # Extend the time and value arrays from their end with fill values
        itime = abs(date_range - f107_times[-1]).argmin() + 1
        extend_times = list(date_range[itime:])
        f107_times.extend(extend_times)
        f107_values.extend([fill_val for kk in extend_times])

    # Save output data
    f107_inst.data = pds.DataFrame(f107_values, columns=['f107'],
                                   index=f107_times)

    # Resample the output data, filling missing values
    if (date_range.shape != f107_inst.index.shape
            or abs(date_range - f107_inst.index).max().total_seconds() > 0.0):
        f107_inst.data = f107_inst.data.resample(freq).fillna(method=None)
        if np.isfinite(fill_val):
            f107_inst.data[np.isnan(f107_inst.data)] = fill_val

    # Update the metadata notes for this procedure
    notes += ", in that order"
    f107_inst.meta['f107'] = {f107_inst.meta.labels.notes: notes}

    return f107_inst


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
        values.extend([np.int64(vv) for vv in split_line[1::2]])

    return dates, values


def rewrite_daily_file(year, outfile, lines):
    """Rewrite the SWPC Daily Solar Data files.

    Parameters
    ----------
    year : int
        Year of data file (format changes based on date)
    outfile : str
        Output filename
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

    # Collect into DataFrame
    data = pds.DataFrame(data_dict, index=solar_times,
                         columns=data_dict.keys())

    # Write out as a file
    data.to_csv(outfile, header=True)

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
            elif((year == 1994 and kk in xray_keys)
                 or (not optical and kk in optical_keys)):
                # X-ray flares in files after 1994, optical flares come later
                val = -1
            else:
                val = split_line[j + 3]
                j += 1

            if kk != 'goes_bgd_flux':
                if val == "*":
                    val = -999 if i < 5 else -1
                else:
                    val = np.int64(val)
            values[kk].append(val)

    return dates, values


def calc_f107a(f107_inst, f107_name='f107', f107a_name='f107a', min_pnts=41):
    """Calculate the 81 day mean F10.7.

    Parameters
    ----------
    f107_inst : pysat.Instrument
        pysat Instrument holding the F10.7 data
    f107_name : str
        Data column name for the F10.7 data (default='f107')
    f107a_name : str
        Data column name for the F10.7a data (default='f107a')
    min_pnts : int
        Minimum number of points required to calculate an average (default=41)

    Note
    ----
    Will not pad data on its own

    """

    # Test to see that the input data is present
    if f107_name not in f107_inst.data.columns:
        raise ValueError("unknown input data column: " + f107_name)

    # Test to see that the output data does not already exist
    if f107a_name in f107_inst.data.columns:
        raise ValueError("output data column already exists: " + f107a_name)

    if f107_name in f107_inst.meta:
        fill_val = f107_inst.meta[f107_name][f107_inst.meta.labels.fill_val]
    else:
        fill_val = np.nan

    # Calculate the rolling mean.  Since these values are centered but rolling
    # function doesn't allow temporal windows to be calculated this way, create
    # a hack for this.
    #
    # Ensure the data are evenly sampled at a daily frequency, since this is
    # how often F10.7 is calculated.
    f107_fill = f107_inst.data.resample('1D').fillna(method=None)

    # Replace the time index with an ordinal
    time_ind = f107_fill.index
    f107_fill['ord'] = pds.Series([tt.toordinal() for tt in time_ind],
                                  index=time_ind)
    f107_fill.set_index('ord', inplace=True)

    # Calculate the mean
    f107_fill[f107a_name] = f107_fill[f107_name].rolling(window=81,
                                                         min_periods=min_pnts,
                                                         center=True).mean()

    # Replace the ordinal index with the time
    f107_fill['time'] = pds.Series(time_ind, index=f107_fill.index)
    f107_fill.set_index('time', inplace=True)

    # Resample to the original frequency, if it is not equal to 1 day
    freq = pysat.utils.time.calc_freq(f107_inst.index)
    if freq != "86400S":
        # Resample to the desired frequency
        f107_fill = f107_fill.resample(freq).ffill()

        # Save the output in a list
        f107a = list(f107_fill[f107a_name])

        # Fill any dates that fall
        time_ind = pds.date_range(f107_fill.index[0], f107_inst.index[-1],
                                  freq=freq)
        for itime in time_ind[f107_fill.index.shape[0]:]:
            if (itime - f107_fill.index[-1]).total_seconds() < 86400.0:
                f107a.append(f107a[-1])
            else:
                f107a.append(fill_val)

        # Redefine the Series
        f107_fill = pds.DataFrame({f107a_name: f107a}, index=time_ind)

    # There may be missing days in the output data, remove these
    if f107_inst.index.shape < f107_fill.index.shape:
        f107_fill = f107_fill.loc[f107_inst.index]

    # Save the data
    f107_inst[f107a_name] = f107_fill[f107a_name]

    # Update the metadata
    meta_dict = {f107_inst.meta.labels.units: 'SFU',
                 f107_inst.meta.labels.name: 'F10.7a',
                 f107_inst.meta.labels.desc: "81-day centered average of F10.7",
                 f107_inst.meta.labels.min_val: 0.0,
                 f107_inst.meta.labels.max_val: np.nan,
                 f107_inst.meta.labels.fill_val: fill_val,
                 f107_inst.meta.labels.notes:
                 ' '.join(('Calculated using data between',
                           '{:} and {:}'.format(f107_inst.index[0],
                                                f107_inst.index[-1])))}

    f107_inst.meta[f107a_name] = meta_dict

    return
