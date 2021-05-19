# -*- coding: utf-8 -*-.
"""Provides default routines for the space weather instruments

"""

import numpy as np


def preprocess(inst):
    """Preprocess the meta data by replacing the file fill values with NaN

    Parameters
    ----------
    inst : pysat.Instrument
        pysat.Instrument object

    """
    # Replace all fill values with NaN
    for col in inst.data.columns:
        fill_val = inst.meta[col][inst.meta.labels.fill_val]
        if ~np.isnan(fill_val):
            inst.data[col] = inst.data[col].replace(fill_val, np.nan)
            inst.meta[col] = {inst.meta.labels.fill_val: np.nan}

    return
