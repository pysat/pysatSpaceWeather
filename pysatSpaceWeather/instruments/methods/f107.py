# -*- coding: utf-8 -*-.
"""Provides default routines for solar wind and geospace indices

"""

import pandas as pds
import numpy as np

import pysat

import pysatSpaceWeather as pysat_sw


def acknowledgements(name, tag):
    """Returns acknowledgements for space weather dataset

    Parameters
    ----------
    name : string
        Name of space weather index, eg, dst, f107, kp
    tag : string
        Tag of the space waether index

    """
    lisird = 'NOAA radio flux obtained through LISIRD'
    swpc = ''.join(['Prepared by the U.S. Dept. of Commerce, NOAA, Space ',
                    'Weather Prediction Center'])

    ackn = {'f107': {'': lisird, 'all': lisird, 'prelim': swpc,
                     'daily': swpc, 'forecast': swpc, '45day': swpc}}

    return ackn[name][tag]


def references(name, tag):
    """Returns references for space weather dataset

    Parameters
    ----------
    name : string
        Name of space weather index, eg, dst, f107, kp
    tag : string
        Tag of the space weather index

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

    refs = {'f107': {'': "\n".join([noaa_desc, orig_ref]),
                     'all': "\n".join([noaa_desc, orig_ref]),
                     'prelim': "\n".join([swpc_desc, orig_ref]),
                     'daily': "\n".join([swpc_desc, orig_ref]),
                     'forecast': "\n".join([swpc_desc, orig_ref]),
                     '45day': "\n".join([swpc_desc, orig_ref])}}

    return refs[name][tag]


def combine_f107(standard_inst, forecast_inst, start=None, stop=None):
    """ Combine the output from the measured and forecasted F10.7 sources

    Parameters
    ----------
    standard_inst : pysat.Instrument or NoneType
        Instrument object containing data for the 'sw' platform, 'f107' name,
        and '', 'all', 'prelim', or 'daily' tag
    forecast_inst : pysat.Instrument or NoneType
        Instrument object containing data for the 'sw' platform, 'f107' name,
        and 'prelim', '45day' or 'forecast' tag
    start : dt.datetime or NoneType
        Starting time for combining data, or None to use earliest loaded
        date from the pysat Instruments (default=None)
    stop : dt.datetime
        Ending time for combining data, or None to use the latest loaded date
        from the pysat Instruments (default=None)

    Returns
    -------
    f107_inst : pysat.Instrument
        Instrument object containing F10.7 observations for the desired period
        of time, merging the standard, 45day, and forecasted values based on
        their reliability

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
    f107_inst.doy = int(start.strftime("%j"))
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
                if standard_inst.tag == 'daily':
                    # Add 30 days
                    standard_inst.load(date=itime + pds.DateOffset(days=30))
                else:
                    standard_inst.load(date=itime)

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
                    forecast_inst.load(fname=filename)

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
                new_times = list(forecast_inst.index[good_times][good_vals])
                f107_times.extend(new_times)
                new_vals = list(forecast_inst['f107'][good_times][good_vals])
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

    # Update the metadata notes for this custom procedure
    notes += ", in that order"
    f107_inst.meta['f107'] = {f107_inst.meta.labels.notes: notes}

    return f107_inst
