#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
#
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# This work was supported by the Office of Naval Research.
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

    def setup_method(self):
        """Create a clean testing setup."""
        # TODO(#131): Remove version check after min version supported is 3.2.0
        inst_kwargs = dict()
        if all([Version(pysat.__version__) > Version('3.0.1'),
                Version(pysat.__version__) < Version('3.2.0')]):
            inst_kwargs['use_header'] = True
        self.testInst = pysat.Instrument('pysat', 'testing', **inst_kwargs)
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
