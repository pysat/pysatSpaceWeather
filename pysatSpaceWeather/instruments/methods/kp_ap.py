#!/usr/bin/env python
# -*- coding: utf-8 -*-.
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
#
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
"""Provides routines to support the geomagnetic indices, Kp and Ap."""

import datetime as dt
import numpy as np
import pandas as pds

import pysat

import pysatSpaceWeather as pysat_sw
from pysatSpaceWeather.instruments.methods import general
from pysatSpaceWeather.instruments.methods import gfz
from pysatSpaceWeather.instruments.methods import swpc


# --------------------------------------------------------------------------
# Instrument utilities

def acknowledgements(name, tag):
    """Define the acknowledgements for the geomagnetic data sets.

    Parameters
    ----------
    name : str
        Instrument name of space weather index, accepts 'kp' or 'ap'.
    tag : str
        Instrument tag.

    """

    ackn = {'kp': {'forecast': swpc.ackn, 'recent': swpc.ackn, 'def': gfz.ackn,
                   'now': gfz.ackn, 'prediction': swpc.ackn},
            'ap': {'forecast': swpc.ackn, 'recent': swpc.ackn,
                   'prediction': swpc.ackn, '45day': swpc.ackn,
                   'def': gfz.ackn, 'now': gfz.ackn},
            'cp': {'def': gfz.ackn, 'now': gfz.ackn}}

    return ackn[name][tag]


def references(name, tag):
    """Define the references for the geomagnetic data sets.

    Parameters
    ----------
    name : str
        Instrument name of space weather index, accepts kp or ap.
    tag : str
        Instrument tag.

    """

    gen_refs = "\n".join([''.join(["J. Bartels, The technique of scaling ",
                                   "indices K and Q of geomagnetic activity, ",
                                   "Ann. Intern. Geophys. Year 4, 215-226, ",
                                   "1957."]),
                          ''.join(["J. Bartels,The geomagnetic measures for ",
                                   "the time-variations of solar corpuscular ",
                                   "radiation, described for use in ",
                                   "correlation studies in other geophysical ",
                                   "fields, Ann. Intern. Geophys. Year 4, ",
                                   "227-236, 1957."]),
                          ''.join(["P.N. Mayaud, Derivation, Meaning and Use ",
                                   "of Geomagnetic Indices, Geophysical ",
                                   "Monograph 22, Am. Geophys. Union, ",
                                   "Washington D.C., 1980."]),
                          ''.join(["G.K. Rangarajan, Indices of magnetic ",
                                   "activity, in Geomagnetism, edited by I.A. ",
                                   "Jacobs, Academic, San Diego, 1989."]),
                          ''.join(["M. Menvielle and A. Berthelier, The ",
                                   "K-derived planetary indices: description ",
                                   "and availability, Rev. Geophys. 29, 3, ",
                                   "415-432, 1991."])])

    refs = {'kp': {'forecast': gen_refs, 'recent': gen_refs,
                   'prediction': gen_refs, 'def': gfz.geoind_refs,
                   'now': gfz.geoind_refs},
            'ap': {'recent': gen_refs, 'forecast': gen_refs, '45day': gen_refs,
                   'prediction': gen_refs, 'def': gfz.geoind_refs,
                   'now': gfz.geoind_refs},
            'cp': {'def': gfz.geoind_refs, 'now': gfz.geoind_refs}}

    return refs[name][tag]


def initialize_kp_metadata(meta, data_key, fill_val=-1):
    """Initialize the Kp meta data using our knowledge of the index.

    Parameters
    ----------
    meta : pysat._meta.Meta
        Pysat Metadata
    data_key : str
        String denoting the data key
    fill_val : int or float
        File-specific fill value (default=-1)

    """

    meta[data_key] = {meta.labels.units: '',
                      meta.labels.name: data_key,
                      meta.labels.desc: "Planetary K-index",
                      meta.labels.min_val: 0,
                      meta.labels.max_val: 9,
                      meta.labels.fill_val: fill_val}

    return


def initialize_ap_metadata(meta, data_key, fill_val=-1):
    """Initialize the ap meta data using our knowledge of the index.

    Parameters
    ----------
    meta : pysat._meta.Meta
        Pysat Metadata
    data_key : str
        String denoting the data key
    fill_val : int or float
        File-specific fill value (default=-1)

    """

    meta[data_key] = {meta.labels.units: '',
                      meta.labels.name: data_key,
                      meta.labels.desc: "ap (equivalent range) index",
                      meta.labels.min_val: 0,
                      meta.labels.max_val: 400,
                      meta.labels.fill_val: fill_val}

    return


def initialize_bartel_metadata(meta, data_key, fill_val=-1):
    """Initialize the Bartel rotation meta data using our knowledge of the data.

    Parameters
    ----------
    meta : pysat._meta.Meta
        Pysat Metadata
    data_key : str
        String denoting the data key
    fill_val : int or float
        File-specific fill value (default=-1)

    """

    if data_key.find('solar_rotation_num') >= 0:
        units = ''
        bname = 'Bartels solar rotation number'
        desc = 'A sequence of 27-day intervals counted from February 8, 1832'
        max_val = np.inf
    elif data_key.find('day_within') >= 0:
        units = 'day'
        bname = 'Days within Bartels solar rotation'
        desc = 'Number of day within the Bartels solar rotation',
        max_val = 27
    else:
        raise ValueError('unknown data key: {:}'.format(data_key))

    meta[data_key] = {meta.labels.units: units,
                      meta.labels.name: bname,
                      meta.labels.desc: desc,
                      meta.labels.min_val: 1,
                      meta.labels.max_val: max_val,
                      meta.labels.fill_val: fill_val}

    return

# --------------------------------------------------------------------------
# Common custom functions


def convert_3hr_kp_to_ap(kp_inst, var_name='Kp'):
    """Calculate 3 hour ap from 3 hour Kp index.

    Parameters
    ----------
    kp_inst : pysat.Instrument
        Instrument containing Kp data
    var_name : str
        Variable name for the Kp data (default='Kp')

    Raises
    ------
    ValueError
        If `var_name` is not present in `kp_inst`.

    Note
    ----
    Conversion between ap and Kp indices is described at:
    https://www.ngdc.noaa.gov/stp/GEOMAG/kp_ap.html

    Assigns new data to '3hr_ap'.

    """

    # Kp are keys, where n.3 = n+ and n.6 = (n+1)-. E.g., 0.6 = 1-
    kp_to_ap = {0: 0, 0.3: 2, 0.6: 3, 1: 4, 1.3: 5, 1.6: 6, 2: 7, 2.3: 9,
                2.6: 12, 3: 15, 3.3: 18, 3.6: 22, 4: 27, 4.3: 32, 4.6: 39,
                5: 48, 5.3: 56, 5.6: 67, 6: 80, 6.3: 94, 6.6: 111, 7: 132,
                7.3: 154, 7.6: 179, 8: 207, 8.3: 236, 8.6: 300, 9: 400}

    def ap(kk):
        if np.isfinite(kk):
            return kp_to_ap[np.floor(kk * 10.0) / 10.0]
        else:
            return np.nan

    # Test the input
    if var_name not in kp_inst.variables:
        raise ValueError('Variable name for Kp data is missing: {:}'.format(
            var_name))

    # Convert from Kp to ap
    fill_val = kp_inst.meta[var_name][kp_inst.meta.labels.fill_val]
    ap_data = np.array([ap(kp) if kp != fill_val else fill_val
                        for kp in kp_inst[var_name]])

    # Append the output to the pysat instrument
    kp_inst['3hr_ap'] = pds.Series(ap_data, index=kp_inst.index)

    # Add metadata
    initialize_ap_metadata(kp_inst.meta, '3hr_ap', fill_val)
    kp_inst.meta['3hr_ap',
                 kp_inst.meta.labels.desc] = "3-hr ap (equivalent range) index"
    kp_inst.meta['3hr_ap', kp_inst.meta.labels.notes] = ''.join([
        'ap converted from Kp as described at: ',
        'https://www.ngdc.noaa.gov/stp/GEOMAG/kp_ap.html'])

    return


def calc_daily_Ap(ap_inst, ap_name='3hr_ap', daily_name='Ap',
                  running_name=None, min_periods=8):
    """Calculate the daily Ap index from the 3hr ap index.

    Parameters
    ----------
    ap_inst : pysat.Instrument
        pysat instrument containing 3-hourly ap data
    ap_name : str
        Column name for 3-hourly ap data (default='3hr_ap')
    daily_name : str
        Column name for daily Ap data (default='Ap')
    running_name : str or NoneType
        Column name for daily running average of ap, not output if None
        (default=None)
    min_periods : int
        Mininmum number of observations needed to output an average value
        (default=8)

    Raises
    ------
    ValueError
        If `ap_name` or `daily_name` aren't present in `ap_inst`

    Note
    ----
    Ap is the mean of the 3hr ap indices measured for a given day

    Option for running average is included since this information is used
    by MSIS when running with sub-daily geophysical inputs

    """

    # Test that the necessary data is available
    if ap_name not in ap_inst.variables:
        raise ValueError("bad 3-hourly ap column name: {:}".format(ap_name))

    # Test to see that we will not be overwritting data
    if daily_name in ap_inst.variables:
        raise ValueError("daily Ap column name already exists: " + daily_name)

    # Calculate the daily mean value
    ap_mean = ap_inst[ap_name].rolling(window='1D',
                                       min_periods=min_periods).mean()

    if running_name is not None:
        ap_inst[running_name] = ap_mean

        initialize_ap_metadata(ap_inst.meta, running_name,
                               ap_inst.meta[ap_name][
                                   ap_inst.meta.labels.fill_val])
        ap_inst.meta[running_name,
                     ap_inst.meta.labels.desc] = "running daily Ap index"
        ap_inst.meta[running_name,
                     ap_inst.meta.labels.notes] = ''.join(['24-h running ave',
                                                           ' of 3-hourly ',
                                                           'ap indices'])

    # Resample, backfilling so that each day uses the mean for the data from
    # that day only
    #
    # Pad the data so the first day will be backfilled
    ap_pad = pds.Series(np.full(shape=(1,), fill_value=np.nan),
                        index=[ap_mean.index[0] - pds.DateOffset(hours=3)])

    # Extract the mean that only uses data for one day
    ap_sel = ap_pad.combine_first(ap_mean.iloc[[i for i, tt in
                                                enumerate(ap_mean.index)
                                                if tt.hour == 21]])

    # Backfill this data
    ap_data = ap_sel.resample('3h').bfill()

    # Save the output for the original time range
    ap_inst[daily_name] = pds.Series(ap_data[1:], index=ap_data.index[1:])

    # Add metadata
    initialize_ap_metadata(ap_inst.meta, 'Ap',
                           ap_inst.meta[ap_name][ap_inst.meta.labels.fill_val])
    ap_inst.meta[daily_name, ap_inst.meta.labels.desc] = "daily Ap index"
    ap_inst.meta[daily_name,
                 ap_inst.meta.labels.notes] = ''.join(['Ap daily mean ',
                                                       'calculated from ',
                                                       '3-hourly ap indices'])
    return


def filter_geomag(inst, min_kp=0, max_kp=9, filter_time=24, kp_inst=None,
                  var_name='Kp'):
    """Filter pysat.Instrument data for given time after Kp drops below gate.

    Parameters
    ----------
    inst : pysat.Instrument or NoneType
        Instrument with non-Kp data to be filtered by geomagnetic activity
    min_kp : float
        Minimum Kp value allowed. Kp values below this filter the data in
        inst (default=0)
    max_kp : float
        Maximum Kp value allowed. Kp values above this filter the data in
        inst (default=9)
    filter_time : int
        Number of hours to filter data after Kp drops below max_kp (default=24)
    kp_inst : pysat.Instrument or NoneType
        Kp pysat.Instrument object with or without data already loaded. If None,
        will load GFZ definitive kp data for the instrument date (default=None)
    var_name : str
        String providing the variable name for the Kp data (default='Kp')

    Raises
    ------
    IOError
        If no Kp data is available to load

    Note
    ----
    Loads Kp data for the same timeframe covered by inst and sets inst.data to
    NaN for times when Kp > max_kp or Kp < min_kp and for filter_time after Kp
    drops below max_kp.

    Default max and min values accept all Kp, so changing only one will cause
    the filter to act as a high- or low-pass function.

    This routine is written for standard Kp data (tags of 'def', 'now'), not
    the forecast or recent data.  However, it will work with these Kp data if
    they are supplied.

    """
    # Load the desired data
    if kp_inst is None:
        kp_inst = pysat.Instrument(inst_module=pysat_sw.instruments.sw_kp,
                                   tag='def', pad=dt.timedelta(days=1))

    if kp_inst.empty:
        load_kwargs = {'date': inst.index[0], 'end_date': inst.index[-1],
                       'verifyPad': True}
        kp_inst.load(**load_kwargs)

    if kp_inst.empty:
        raise IOError(
            'unable to load {:} data for {:}-{:}, check local data'.format(
                ':'.join([inst.platform, inst.name, inst.tag, inst.inst_id]),
                inst.index[0], inst.index[-1]))

    # Begin filtering, starting at the beginning of the instrument data
    sel_data = kp_inst[(inst.index[0] - dt.timedelta(days=1)):
                       (inst.index[-1] + dt.timedelta(days=1))]
    ind, = np.where((sel_data[var_name] > max_kp)
                    | (sel_data[var_name] < min_kp))

    for lind in ind:
        # Determine the time filter range for removing each flagged data
        sind = sel_data.index[lind]
        eind = sind + pds.DateOffset(hours=filter_time)
        inst[sind:eind] = np.nan
        inst.data = inst.data.dropna(axis=0, how='all')

    return


# --------------------------------------------------------------------------
# Common analysis functions

def convert_ap_to_kp(ap_data, fill_val=-1, ap_name='ap', kp_name='Kp'):
    """Convert Ap into Kp.

    Parameters
    ----------
    ap_data : array-like
        Array-like object containing Ap data
    fill_val : int, float, NoneType
        Fill value for the data set (default=-1)
    ap_name : str
        Name of the input ap (default='ap')
    kp_name : str
        Name of the output Kp (default='Kp')

    Returns
    -------
    kp_data : array-like
        Array-like object containing Kp data
    meta : Metadata
        Metadata object containing information about transformed data

    """

    # Convert from ap to Kp
    kp_data = np.array([round_ap(aa, fill_val=fill_val) for aa in ap_data])

    # Set the metadata
    meta = pysat.Meta()
    initialize_kp_metadata(meta, 'Kp', fill_val)
    meta['Kp', meta.labels.desc] = 'Kp converted from {:}'.format(ap_name)
    meta['Kp', meta.labels.notes] = ''.join(
        ['Kp converted from ', ap_name, 'as described at: ',
         'https://www.ngdc.noaa.gov/stp/GEOMAG/kp_ap.html'])

    # Return data and metadata
    return kp_data, meta


def round_ap(ap_in, fill_val=np.nan):
    """Round an ap value to the nearest Kp value.

    Parameters
    ----------
    ap_in : float
        Ap value as a floating point number.
    fill_val : float
        Value for unassigned or bad indices. (default=np.nan)

    Returns
    -------
    float
        Fill value for infinite or out-of-range data, otherwise the best kp
        index is provided.

    """

    # Define the ap to kp conversion
    one_third = 1.0 / 3.0
    two_third = 2.0 / 3.0
    ap_to_kp = {0: 0, 2: one_third, 3: two_third, 4: 1, 5: 1.0 + one_third,
                6: 1.0 + two_third, 7: 2, 9: 2.0 + one_third,
                12: 2.0 + two_third, 15: 3, 18: 3.0 + one_third,
                22: 3.0 + two_third, 27: 4, 32: 4.0 + one_third,
                39: 4.0 + two_third, 48: 5, 56: 5.0 + one_third,
                67: 5.0 + two_third, 80: 6, 94: 6.0 + one_third,
                111: 6.0 + two_third, 132: 7, 154: 7.0 + one_third,
                179: 7.0 + two_third, 207: 8, 236: 8.0 + one_third,
                300: 8.0 + two_third, 400: 9}
    max_ap = 400

    # Infinite or NaN values will return the fill value
    if not np.isfinite(ap_in):
        return fill_val

    # Ap values that correspond exactly to a Kp value will return that value
    if ap_in in ap_to_kp.keys():
        return ap_to_kp[ap_in]

    # The input Ap value may be appropriate, but does not correspond directly
    # to a Kp index.  Get a sorted list of directly corresponding Ap indices,
    # with Kp returned as double (N- = N.6667, N+ = N.3333333)
    ap_keys = sorted([akey for akey in ap_to_kp.keys() if akey <= ap_in])

    # If the value is too large or too small, return the fill value
    if len(ap_keys) == 0 or (ap_keys[-1] < ap_in and ap_keys[-1] == max_ap):
        return fill_val

    # The value is realistic, return the Kp value
    return ap_to_kp[ap_keys[-1]]


def combine_kp(standard_inst=None, recent_inst=None, forecast_inst=None,
               start=None, stop=None, fill_val=np.nan):
    """Combine the output from the different Kp sources for a range of dates.

    Parameters
    ----------
    standard_inst : pysat.Instrument or NoneType
        Instrument object containing data for the 'sw' platform, 'kp' name,
        and 'def' tag or None to exclude (default=None)
    recent_inst : pysat.Instrument or NoneType
        Instrument object containing data for the 'sw' platform, 'kp' name,
        and 'recent' tag or None to exclude (default=None)
    forecast_inst : pysat.Instrument or NoneType
        Instrument object containing data for the 'sw' platform, 'kp' name,
        and 'forecast' tag or None to exclude (default=None)
    start : dt.datetime or NoneType
        Starting time for combining data, or None to use earliest loaded
        date from the pysat Instruments (default=None)
    stop : dt.datetime
        Ending time for combining data, or None to use the latest loaded date
        from the pysat Instruments (default=None)
    fill_val : int or float
        Desired fill value (since the standard instrument fill value differs
        from the other sources) (default=np.nan)

    Returns
    -------
    kp_inst : pysat.Instrument
        Instrument object containing Kp observations for the desired period of
        time, merging the standard, recent, and forecasted values based on
        their reliability

    Raises
    ------
    ValueError
        If only one Kp instrument or bad times are provided

    Note
    ----
    Merging prioritizes the standard data, then the recent data, and finally
    the forecast data.

    Will not attempt to download any missing data, but will load data.

    If no data is present, but dates are provided, supplies a series of fill
    values.

    """

    notes = "Combines data from"

    # Create an ordered list of the Instruments, excluding any that are None
    all_inst = list()
    tag = 'combined'
    inst_flag = None
    if standard_inst is not None:
        all_inst.append(standard_inst)
        tag += '_standard'
        if inst_flag is None:
            inst_flag = 'standard'

    if recent_inst is not None:
        all_inst.append(recent_inst)
        tag += '_recent'
        if inst_flag is None:
            inst_flag = 'recent'

    if forecast_inst is not None:
        all_inst.append(forecast_inst)
        tag += '_forecast'
        if inst_flag is None:
            inst_flag = 'forecast'

    if len(all_inst) < 2:
        raise ValueError("need at two Kp Instrument objects to combine them")

    # If the start or stop times are not defined, get them from the Instruments
    if start is None:
        stimes = [inst.index.min() for inst in all_inst if len(inst.index) > 0]
        start = min(stimes) if len(stimes) > 0 else None

    if stop is None:
        stimes = [inst.index.max() for inst in all_inst if len(inst.index) > 0]
        stop = max(stimes) + dt.timedelta(days=1) if len(stimes) > 0 else None

    if start is None or stop is None:
        raise ValueError(' '.join(("must either load in Instrument objects or",
                                   "provide starting and ending times")))

    # Initialize the output instrument
    meta_kwargs = all_inst[0].meta_kwargs
    kp_inst = pysat.Instrument(meta_kwargs=meta_kwargs)

    kp_inst.inst_module = pysat_sw.instruments.sw_kp
    kp_inst.tag = tag
    kp_inst.date = start
    kp_inst.doy = np.int64(start.strftime("%j"))
    kp_inst.meta = pysat.Meta(**meta_kwargs)
    initialize_kp_metadata(kp_inst.meta, 'Kp', fill_val=fill_val)

    kp_times = list()
    kp_values = list()

    # Cycle through the desired time range
    itime = start
    while itime < stop and inst_flag is not None:
        # Load and save the standard data for as many times as possible
        if inst_flag == 'standard':
            # Test to see if data loading is needed
            if not np.any(standard_inst.index == itime):
                standard_inst.load(date=itime)

            if notes.find("standard") < 0:
                notes += " the {:} source ({:} to ".format(inst_flag,
                                                           itime.date())

            if len(standard_inst.index) == 0:
                inst_flag = 'forecast' if recent_inst is None else 'recent'
                notes += "{:})".format(itime.date())
            else:
                local_fill_val = standard_inst.meta[
                    'Kp', standard_inst.meta.labels.fill_val]
                good_times = ((standard_inst.index >= itime)
                              & (standard_inst.index < stop))
                good_vals = np.array([
                    not general.is_fill_val(val, local_fill_val)
                    for val in standard_inst['Kp'][good_times]])
                new_times = list(standard_inst.index[good_times][good_vals])

                if len(new_times) > 0:
                    kp_times.extend(new_times)
                    kp_values.extend(list(
                        standard_inst['Kp'][good_times][good_vals]))
                    itime = kp_times[-1] + pds.DateOffset(hours=3)
                else:
                    inst_flag = 'forecast' if recent_inst is None else 'recent'
                    notes += "{:})".format(itime.date())

        # Load and save the recent data for as many times as possible
        if inst_flag == 'recent':
            # Determine which files should be loaded
            if len(recent_inst.index) == 0:
                if len(recent_inst.files.files) > 0:
                    files = np.unique(recent_inst.files.files[itime:stop])
                else:
                    files = [None]  # No files available
            else:
                files = [None]  # No load needed, if already initialized

            # Cycle through all possible files of interest, saving relevant
            # data
            for filename in files:
                if filename is not None:
                    recent_inst.load(fname=filename)

                if notes.find("recent") < 0:
                    notes += " the {:} source ({:} to ".format(inst_flag,
                                                               itime.date())

                # Determine which times to save
                if recent_inst.empty:
                    new_times = []
                else:
                    local_fill_val = recent_inst.meta[
                        'Kp', recent_inst.meta.labels.fill_val]
                    good_times = ((recent_inst.index >= itime)
                                  & (recent_inst.index < stop))
                    good_vals = np.array([
                        not general.is_fill_val(val, local_fill_val)
                        for val in recent_inst['Kp'][good_times]])
                    new_times = list(recent_inst.index[good_times][good_vals])

                # Save output data and cycle time
                if len(new_times) > 0:
                    kp_times.extend(new_times)
                    kp_values.extend(list(
                        recent_inst['Kp'][good_times][good_vals]))
                    itime = kp_times[-1] + pds.DateOffset(hours=3)

            inst_flag = 'forecast' if forecast_inst is not None else None
            notes += "{:})".format(itime.date())

        # Load and save the forecast data for as many times as possible
        if inst_flag == "forecast":
            # Determine which files should be loaded
            if len(forecast_inst.index) == 0:
                if len(forecast_inst.files.files) > 0:
                    files = np.unique(forecast_inst.files.files[itime:stop])
                else:
                    files = [None]  # No files have been downloaded
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

                # Determine which times to save
                if not forecast_inst.empty:
                    local_fill_val = forecast_inst.meta[
                        'Kp', forecast_inst.meta.labels.fill_val]
                    good_times = ((forecast_inst.index >= itime)
                                  & (forecast_inst.index < stop))
                    good_vals = np.array([
                        not general.is_fill_val(val, local_fill_val)
                        for val in forecast_inst['Kp'][good_times]])

                    # Save desired data
                    new_times = list(forecast_inst.index[good_times][good_vals])

                    if len(new_times) > 0:
                        kp_times.extend(new_times)
                        new_vals = list(forecast_inst['Kp'][good_times][
                            good_vals])
                        kp_values.extend(new_vals)

                        # Cycle time
                        itime = kp_times[-1] + pds.DateOffset(hours=3)
            notes += "{:})".format(itime.date())

            inst_flag = None

    if inst_flag is not None:
        notes += "{:})".format(itime.date())

    # Determine if the beginning or end of the time series needs to be padded
    freq = None if len(kp_times) < 2 else pysat.utils.time.calc_freq(kp_times)
    end_date = stop - pds.DateOffset(days=1)
    date_range = pds.date_range(start=start, end=end_date, freq=freq)

    if len(kp_times) == 0:
        kp_times = date_range

    if date_range[0] < kp_times[0]:
        # Extend the time and value arrays from their beginning with fill
        # values
        itime = abs(date_range - kp_times[0]).argmin()
        kp_times.reverse()
        kp_values.reverse()
        extend_times = list(date_range[:itime])
        extend_times.reverse()
        kp_times.extend(extend_times)
        kp_values.extend([fill_val for kk in extend_times])
        kp_times.reverse()
        kp_values.reverse()

    if date_range[-1] > kp_times[-1]:
        # Extend the time and value arrays from their end with fill values
        itime = abs(date_range - kp_times[-1]).argmin() + 1
        extend_times = list(date_range[itime:])
        kp_times.extend(extend_times)
        kp_values.extend([fill_val for kk in extend_times])

    # Save output data
    kp_inst.data = pds.DataFrame(kp_values, columns=['Kp'], index=kp_times)

    # Resample the output data, filling missing values
    if (date_range.shape != kp_inst.index.shape
            or abs(date_range - kp_inst.index).max().total_seconds() > 0.0):
        kp_inst.data = kp_inst.data.resample(freq).asfreq()
        if np.isfinite(fill_val):
            kp_inst.data[np.isnan(kp_inst.data)] = fill_val

    # Update the metadata notes for this procedure
    notes += ", in that order"
    kp_inst.meta['Kp', kp_inst.meta.labels.notes] = notes

    return kp_inst
