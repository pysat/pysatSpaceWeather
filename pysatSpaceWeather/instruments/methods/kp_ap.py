# -*- coding: utf-8 -*-.
"""Provides default routines for solar wind and geospace indices

"""

import pandas as pds
import numpy as np

import pysat

import pysatSpaceWeather as pysat_sw


# --------------------------------------------------------------------------
# Instrument utilities

def acknowledgements(name, tag):
    """Returns acknowledgements for space weather dataset

    Parameters
    ----------
    name : string
        Name of space weather index, eg, dst, f107, kp
    tag : string
        Tag of the space waether index

    """
    swpc = ''.join(['Prepared by the U.S. Dept. of Commerce, NOAA, Space ',
                    'Weather Prediction Center'])

    ackn = {'kp': {'': 'Provided by GFZ German Research Centre for Geosciences',
                   'forecast': swpc, 'recent': swpc}}

    return ackn[name][tag]


def references(name, tag):
    """Returns references for space weather dataset

    Parameters
    ----------
    name : string
        Name of space weather index, eg, dst, f107, kp
    tag : string
        Tag of the space waether index

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
    refs = {'kp': {'': gen_refs, 'forecast': gen_refs, 'recent': gen_refs}}

    return refs[name][tag]


def initialize_kp_metadata(meta, data_key, fill_val=-1):
    """ Initialize the Kp meta data using our knowledge of the index

    Parameters
    ----------
    meta : pysat._meta.Meta
        Pysat Metadata
    data_key : str
        String denoting the data key
    fill_val : int or float
        File-specific fill value (default=-1)

    """

    meta[data_key] = {meta.labels.name: data_key,
                      meta.labels.desc: "Planetary K-index",
                      meta.labels.min_val: 0,
                      meta.labels.max_val: 9,
                      meta.labels.fill_val: fill_val}

    return


# --------------------------------------------------------------------------
# Common custom functions


def convert_ap_to_kp(ap_data, fill_val=-1, ap_name='ap'):
    """ Convert Ap into Kp

    Parameters
    ----------
    ap_data : array-like
        Array-like object containing Ap data
    fill_val : int, float, NoneType
        Fill value for the data set (default=-1)
    ap_name : str
        Name of the input ap

    Returns
    -------
    kp_data : array-like
        Array-like object containing Kp data
    meta : Metadata
        Metadata object containing information about transformed data

    """

    # Ap are keys, Kp returned as double (N- = N.6667, N+=N.3333333)
    one_third = 1.0 / 3.0
    two_third = 2.0 / 3.0
    ap_to_kp = {0: 0, 2: one_third, 3: two_third,
                4: 1, 5: 1.0 + one_third, 6: 1.0 + two_third,
                7: 2, 9: 2.0 + one_third, 12: 2.0 + two_third,
                15: 3, 18: 3.0 + one_third, 22: 3.0 + two_third,
                27: 4, 32: 4.0 + one_third, 39: 4.0 + two_third,
                48: 5, 56: 5.0 + one_third, 67: 5.0 + two_third,
                80: 6, 94: 6.0 + one_third, 111: 6.0 + two_third,
                132: 7, 154: 7.0 + one_third, 179: 7.0 + two_third,
                207: 8, 236: 8.0 + one_third, 300: 8.0 + two_third,
                400: 9}
    ap_keys = sorted([akey for akey in ap_to_kp.keys()])

    # If the ap falls between two Kp indices, assign it to the lower Kp value
    def round_ap(ap_in, fill_val=fill_val):
        """ Round an ap value to the nearest Kp value
        """
        if not np.isfinite(ap_in):
            return fill_val

        i = 0
        while ap_keys[i] <= ap_in:
            i += 1
        i -= 1

        if i >= len(ap_keys) or ap_keys[i] > ap_in:
            return fill_val

        return ap_to_kp[ap_keys[i]]

    # Convert from ap to Kp
    kp_data = np.array([ap_to_kp[aa] if aa in ap_keys else
                        round_ap(aa, fill_val=fill_val) for aa in ap_data])

    # Set the metadata
    meta = pysat.Meta()
    meta['Kp'] = {meta.labels.name: 'Kp',
                  meta.labels.desc: 'Kp converted from {:}'.format(ap_name),
                  meta.labels.min_val: 0,
                  meta.labels.max_val: 9,
                  meta.labels.fill_val: fill_val,
                  meta.labels.notes: ''.join(
                      ['Kp converted from ', ap_name, 'as described at: ',
                       'https://www.ngdc.noaa.gov/stp/GEOMAG/kp_ap.html'])}

    # Return data and metadata
    return(kp_data, meta)


def convert_3hr_kp_to_ap(kp_inst):
    """ Calculate 3 hour ap from 3 hour Kp index

    Parameters
    ----------
    kp_inst : pysat.Instrument
        Pysat instrument containing Kp data

    Notes
    -----
    Conversion between ap and Kp indices is described at:
    https://www.ngdc.noaa.gov/stp/GEOMAG/kp_ap.html

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
    if 'Kp' not in kp_inst.data.columns:
        raise ValueError('unable to locate Kp data')

    # Convert from Kp to ap
    fill_val = kp_inst.meta['Kp'][kp_inst.meta.labels.fill_val]
    ap_data = np.array([ap(kp) if kp != fill_val else fill_val
                        for kp in kp_inst['Kp']])

    # Append the output to the pysat instrument
    kp_inst['3hr_ap'] = pds.Series(ap_data, index=kp_inst.index)

    # Add metadata
    meta_dict = {kp_inst.meta.labels.name: 'ap',
                 kp_inst.meta.labels.desc: "3-hour ap (equivalent range) index",
                 kp_inst.meta.labels.min_val: 0,
                 kp_inst.meta.labels.max_val: 400,
                 kp_inst.meta.labels.fill_val: fill_val,
                 kp_inst.meta.labels.notes: ''.join(
                     ['ap converted from Kp as described at: ',
                      'at: https://www.ngdc.noaa.gov/stp/GEOMAG/kp_ap.html'])}

    kp_inst.meta['3hr_ap'] = meta_dict


def calc_daily_Ap(ap_inst, ap_name='3hr_ap', daily_name='Ap',
                  running_name=None):
    """ Calculate the daily Ap index from the 3hr ap index

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

    Note
    ----
    Ap is the mean of the 3hr ap indices measured for a given day

    Option for running average is included since this information is used
    by MSIS when running with sub-daily geophysical inputs

    """

    # Test that the necessary data is available
    if ap_name not in ap_inst.data.columns:
        raise ValueError("bad 3-hourly ap column name: {:}".format(ap_name))

    # Test to see that we will not be overwritting data
    if daily_name in ap_inst.data.columns:
        raise ValueError("daily Ap column name already exists: " + daily_name)

    # Calculate the daily mean value
    ap_mean = ap_inst[ap_name].rolling(window='1D', min_periods=8).mean()

    if running_name is not None:
        ap_inst[running_name] = ap_mean

        meta_dict = {ap_inst.meta.labels.name: running_name,
                     ap_inst.meta.labels.desc: "running daily Ap index",
                     ap_inst.meta.labels.min_val: 0,
                     ap_inst.meta.labels.max_val: 400,
                     ap_inst.meta.labels.fill_val:
                     ap_inst.meta[ap_name][ap_inst.meta.labels.fill_val],
                     ap_inst.meta.labels.notes:
                     '24-h running average of 3-hourly ap indices'}

        ap_inst.meta[running_name] = meta_dict

    # Resample, backfilling so that each day uses the mean for the data from
    # that day only
    #
    # Pad the data so the first day will be backfilled
    ap_pad = pds.Series(np.full(shape=(1,), fill_value=np.nan),
                        index=[ap_mean.index[0] - pds.DateOffset(hours=3)])
    # Extract the mean that only uses data for one day
    ap_sel = ap_pad.combine_first(ap_mean[[i for i, tt in
                                           enumerate(ap_mean.index)
                                           if tt.hour == 21]])
    # Backfill this data
    ap_data = ap_sel.resample('3H').backfill()

    # Save the output for the original time range
    ap_inst[daily_name] = pds.Series(ap_data[1:], index=ap_data.index[1:])

    # Add metadata
    meta_dict = {ap_inst.meta.labels.units: '',
                 ap_inst.meta.labels.name: 'Ap',
                 ap_inst.meta.labels.desc: "daily Ap index",
                 ap_inst.meta.labels.min_val: 0,
                 ap_inst.meta.labels.max_val: 400,
                 ap_inst.meta.labels.fill_val:
                 ap_inst.meta[ap_name][ap_inst.meta.labels.fill_val],
                 ap_inst.meta.labels.notes: ''.join(['Ap daily mean calculated',
                                                     ' from 3-hourly ap ',
                                                     'indices'])}

    ap_inst.meta[daily_name] = meta_dict

    return


def filter_geomag(inst, min_kp=0, max_kp=9, filter_time=24, kp_inst=None):
    """Filters pysat.Instrument data for given time after Kp drops below gate.

    Parameters
    ----------
    inst : pysat.Instrument
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
        will load GFZ historic kp data for the instrument date (default=None)

    Note
    ----
    Loads Kp data for the same timeframe covered by inst and sets inst.data to
    NaN for times when Kp > max_kp or Kp < min_kp and for filter_time after Kp
    drops below max_kp.

    Default max and min values accept all Kp, so changing only one will cause
    the filter to act as a high- or low-pass function.

    This routine is written for standard Kp data (tag=''), not the forecast or
    recent data.  However, it will work with these Kp data if they are supplied.

    This routine is designed to be used with the 'modify' flag if applied as
    a custom routine.

    """
    # Load the desired data
    if kp_inst is None:
        kp_inst = pysat.Instrument(inst_module=pysat_sw.instruments.sw_kp,
                                   tag='', pad=pds.DateOffset(days=1))

    if kp_inst.empty:
        kp_inst.load(date=inst.date, verifyPad=True)

    # Begin filtering, starting at the beginning of the instrument data
    sel_data = kp_inst[(inst.date - pds.DateOffset(days=1)):
                       (inst.date + pds.DateOffset(days=1))]
    ind, = np.where((sel_data['Kp'] > max_kp) | (sel_data['Kp'] < min_kp))
    for lind in ind:
        sind = sel_data.index[lind]
        eind = sind + pds.DateOffset(hours=filter_time)
        inst[sind:eind] = np.nan
        inst.data = inst.data.dropna(axis=0, how='all')

    return


# --------------------------------------------------------------------------
# Common analysis functions


def combine_kp(standard_inst=None, recent_inst=None, forecast_inst=None,
               start=None, stop=None, fill_val=np.nan):
    """ Combine the output from the different Kp sources for a range of dates

    Parameters
    ----------
    standard_inst : pysat.Instrument or NoneType
        Instrument object containing data for the 'sw' platform, 'kp' name,
        and '' tag or None to exclude (default=None)
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

    Note
    ----
    Merging prioritizes the standard data, then the recent data, and finally
    the forecast data

    Will not attempt to download any missing data, but will load data

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
        stop = max(stimes) if len(stimes) > 0 else None
        stop += pds.DateOffset(days=1)

    if start is None or stop is None:
        raise ValueError(' '.join(("must either load in Instrument objects or",
                                   "provide starting and ending times")))

    # Initialize the output instrument
    kp_inst = pysat.Instrument(labels=all_inst[0].meta_labels)
    kp_inst.inst_module = pysat_sw.instruments.sw_kp
    kp_inst.tag = tag
    kp_inst.date = start
    kp_inst.doy = int(start.strftime("%j"))
    kp_inst.meta = pysat.Meta(labels=kp_inst.meta_labels)
    initialize_kp_metadata(kp_inst.meta, 'Kp', fill_val=fill_val)

    kp_times = list()
    kp_values = list()

    # Cycle through the desired time range
    itime = start
    while itime < stop and inst_flag is not None:
        # Load and save the standard data for as many times as possible
        if inst_flag == 'standard':
            standard_inst.load(date=itime)

            if notes.find("standard") < 0:
                notes += " the {:} source ({:} to ".format(inst_flag,
                                                           itime.date())

            if len(standard_inst.index) == 0:
                inst_flag = 'forecast' if recent_inst is None else 'recent'
                notes += "{:})".format(itime.date())
            else:
                kp_times.extend(list(standard_inst.index))
                kp_values.extend(list(standard_inst['Kp']))
                itime = kp_times[-1] + pds.DateOffset(hours=3)

        # Load and save the recent data for as many times as possible
        if inst_flag == 'recent':
            # Determine which files should be loaded
            if len(recent_inst.index) == 0:
                files = np.unique(recent_inst.files.files[itime:stop])
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
                local_fill_val = recent_inst.meta[
                    'Kp', recent_inst.meta.labels.fill_val]
                good_times = ((recent_inst.index >= itime)
                              & (recent_inst.index < stop))
                good_vals = recent_inst['Kp'][good_times] != local_fill_val

                # Save output data and cycle time
                kp_times.extend(list(recent_inst.index[good_times][good_vals]))
                kp_values.extend(list(recent_inst['Kp'][good_times][good_vals]))
                itime = kp_times[-1] + pds.DateOffset(hours=3)

            inst_flag = 'forecast' if forecast_inst is not None else None
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

                # Determine which times to save
                local_fill_val = forecast_inst.meta[
                    'Kp', forecast_inst.meta.labels.fill_val]
                good_times = ((forecast_inst.index >= itime)
                              & (forecast_inst.index < stop))
                good_vals = forecast_inst['Kp'][good_times] != local_fill_val

                # Save desired data and cycle time
                new_times = list(forecast_inst.index[good_times][good_vals])
                kp_times.extend(new_times)
                new_vals = list(forecast_inst['Kp'][good_times][good_vals])
                kp_values.extend(new_vals)
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
        kp_inst.data = kp_inst.data.resample(freq).fillna(method=None)
        if np.isfinite(fill_val):
            kp_inst.data[np.isnan(kp_inst.data)] = fill_val

    # Update the metadata notes for this custom procedure
    notes += ", in that order"
    kp_inst.meta['Kp', kp_inst.meta.labels.notes] = notes

    return kp_inst
