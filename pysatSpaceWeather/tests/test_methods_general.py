#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
#
# Review Status for Classified or Controlled Information by NRL
# -------------------------------------------------------------
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
"""Integration and unit test suite for ACE methods."""

import numpy as np
import pytest

import pysat

from pysatSpaceWeather.instruments.methods import general


class TestGeneralMethods(object):
    """Test class for general methods."""

    def setup_method(self):
        """Create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing')
        self.testInst.load(date=self.testInst.inst_module._test_dates[''][''])
        self.var = self.testInst.variables[0]
        return

    def teardown_method(self):
        """Clean up previous testing setup."""
        del self.testInst, self.var
        return

    def test_preprocess(self):
        """Test the preprocessing routine updates all fill values to be NaN."""

        # Make sure at least one fill value is not already NaN
        self.testInst.meta[self.var] = {self.testInst.meta.labels.fill_val: 0.0}

        # Update the meta data using the general preprocess routine
        general.preprocess(self.testInst)

        # Test the output
        assert np.isnan(
            self.testInst.meta[self.var, self.testInst.meta.labels.fill_val])
        return

    @pytest.mark.parametrize("fill_val", [-1.0, -1, np.nan, np.inf, ''])
    def test_is_fill(self, fill_val):
        """Test the successful evaluation of fill values.

        Parameters
        ----------
        fill_val : float, int, or str
            Fill value to use as a comparison

        """
        # Set the data value to not be a fill value
        if fill_val != '':
            self.var = -47

        # Evaluate the variable is False
        assert not general.is_fill_val(self.var, fill_val)

        # Evaluate the fill value is a fill value
        assert general.is_fill_val(fill_val, fill_val)
        return
