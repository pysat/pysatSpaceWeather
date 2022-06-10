#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
# ----------------------------------------------------------------------------
"""Integration and unit test suite for ACE methods."""

import numpy as np
from packaging.version import Version
import pysat
import pytest

from pysatSpaceWeather.instruments.methods import general


@pytest.mark.skipif(Version(pysat.__version__) < Version('3.0.2'),
                    reason="Test setup requires pysat 3.0.2+")
class TestGeneralMethods(object):
    """Test class for general methods."""

    def setup(self):
        """Create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing')
        self.testInst.load(date=self.testInst.inst_module._test_dates[''][''])
        return

    def teardown(self):
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
        for var in self.testInst.meta.keys():
            assert np.isnan(
                self.testInst.meta[var, self.testInst.meta.labels.fill_val])
        return
