#!/usr/bin/env python
# -*- coding: utf-8 -*-.
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
#
# Review Status for Classified or Controlled Information by NRL
# -------------------------------------------------------------
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
"""Tests for the LISIRD functions."""

import datetime as dt
import logging
import pytest

from pysatSpaceWeather.instruments.methods import lisird
from pysatSpaceWeather import test_data_path


class TestLISIRDFunctions(object):
    """Unit tests for LISIRD functions."""

    def setup_method(self):
        """Create the test environment."""
        self.in_args = [[dt.datetime(2001, 1, 1)], test_data_path, 'test_',
                        '%Y-%m-%d', 'sorce_mg_index',
                        dt.timedelta(seconds=86399)]
        return

    def teardown_method(self):
        """Clean up the test environment."""

        del self.in_args
        return

    def test_download_empty_file(self, caplog):
        """Test a logger warning is raised when no data is found."""

        with caplog.at_level(logging.WARNING, logger='pysat'):
            lisird.download(*self.in_args)

        # Test the warning
        captured = caplog.text
        assert captured.find('no data for') >= 0
        return

    def test_download_bad_fill_columns(self):
        """Test raises KeyError with unexpected column names from fill_vals."""

        self.in_args[0][0] += dt.timedelta(weeks=160)

        with pytest.raises(KeyError) as kerr:
            lisird.download(*self.in_args, fill_vals={"NOPE": -999.0})

        assert str(kerr).find('unknown fill value variable name supplied') >= 0
        return
