# -*- coding: utf-8 -*-.
"""Provides routines that support general space weather instruments."""

import importlib
import numpy as np

import pysat


def preprocess(inst):
    """Preprocess the meta data by replacing the file fill values with NaN.

    Parameters
    ----------
    inst : pysat.Instrument
        pysat.Instrument object

    """

    # Replace all fill values with NaN
    for col in inst.variables:
        fill_val = inst.meta[col, inst.meta.labels.fill_val]

        # Ensure we are dealing with a float for future nan comparison
        if isinstance(fill_val, np.floating) or isinstance(fill_val, float):
            if ~np.isnan(fill_val):
                inst.data[col] = inst.data[col].replace(fill_val, np.nan)
                inst.meta[col] = {inst.meta.labels.fill_val: np.nan}

    return


def get_instrument_data_path(inst_mod_name, tag='', inst_id='', **kwargs):
    """Get the `data_path` attribute from an Instrument sub-module.

    Parameters
    ----------
    inst_mod_name : str
        pysatSpaceWeather Instrument module name
    tag : str
        String specifying the Instrument tag (default='')
    inst_id : str
        String specifying the instrument identification (default='')
    kwargs : dict
        Optional additional kwargs that may be used to initialize an Instrument

    Returns
    -------
    data_path : str
        Path where the Instrument data is stored

    """

    # Import the desired instrument module by name
    inst_mod = importlib.import_module(".".join(["pysatSpaceWeather",
                                                 "instruments", inst_mod_name]))

    # Initialize a temporary instrument to obtain pysat configuration
    temp_inst = pysat.Instrument(inst_module=inst_mod, tag=tag, inst_id=inst_id,
                                 **kwargs)

    # Save the data path for this Instrument down to the inst_id level
    data_path = temp_inst.files.data_path

    # Delete the temporary instrument
    del temp_inst

    return data_path
