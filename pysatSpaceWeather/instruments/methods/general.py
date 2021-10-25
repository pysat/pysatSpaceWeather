# -*- coding: utf-8 -*-.
"""Provides routines that support general space weather instruments."""

import numpy as np


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
