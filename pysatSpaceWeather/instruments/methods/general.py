#!/usr/bin/env python
# -*- coding: utf-8 -*-.
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
#
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
"""Provides routines that support general space weather instruments."""

import importlib
import numpy as np
import os
import requests

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


def get_local_or_remote_text(url, mock_download_dir, filename):
    """Retrieve text from a remote or local file.

    Parameters
    ----------
    filename : str
        Filename without any directory structure
    url : str
        Remote URL where file is located
    mock_download_dir : str or NoneType
        Local directory with downloaded files or None. If not None, will
        process any files with the correct name and date as if they were
        downloaded (default=None)

    Returns
    -------
    raw_txt : str or NoneType
        All the text from the desired file or None if the file could not be
        retrieved

    Raises
    ------
    IOError
        If an unknown mock download directory is supplied.

    """
    if mock_download_dir is None:
        # Set the download webpage
        furl = ''.join([url, filename])
        req = requests.get(furl)

        if req.text.find('not found on this server') > 0:
            # Ensure useful information about server is passed on to user
            pysat.logger.warning('File {:} not found: {:}'.format(filename,
                                                                  url))
            raw_txt = None
        else:
            raw_txt = req.text if req.ok else None
    else:
        if not os.path.isdir(mock_download_dir):
            raise IOError('file location is not a directory: {:}'.format(
                mock_download_dir))

        furl = os.path.join(mock_download_dir, filename)

        if os.path.isfile(furl):
            with open(furl, 'r') as fpin:
                raw_txt = fpin.read()
        else:
            raw_txt = None

    return raw_txt
