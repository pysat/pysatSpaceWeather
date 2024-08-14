#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
#
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
"""Integration and unit test suite for ACE methods."""

import numpy as np

import pysat

from pysatSpaceWeather.instruments.methods import general


class TestGeneralMethods(object):
    """Test class for general methods."""

    def setup_method(self):
        """Create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing')
        self.testInst.load(date=self.testInst.inst_module._test_dates[''][''])
        return

    def teardown_method(self):
        """Clean up previous testing setup."""
        del self.testInst
        return

    def test_preprocess(self):
        """Test the preprocessing routine updates all fill values to be NaN."""

        # Make sure at least one fill value is not already NaN
        var = self.testInst.variables[0]
        self.testInst.meta[var] = {self.testInst.meta.labels.fill_val: 0.0}

        # Update the meta data using the general preprocess routine
        general.preprocess(self.testInst)

        # Test the output
        assert np.isnan(
            self.testInst.meta[var, self.testInst.meta.labels.fill_val])
        return
