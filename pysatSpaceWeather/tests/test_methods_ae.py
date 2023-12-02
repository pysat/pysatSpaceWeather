#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
#
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# This work was supported by the Office of Naval Research.
# ----------------------------------------------------------------------------
"""Integration and unit test suite for AE methods."""

import pytest

from pysatSpaceWeather.instruments.methods import auroral_electrojet as mm_ae


class TestAEMethods(object):
    """Test class for the auroral electrojet methods."""

    def setup_method(self):
        """Create a clean testing setup."""
        self.out = None
        return

    def teardown_method(self):
        """Clean up previous testing setup."""
        del self.out
        return

    @pytest.mark.parametrize('name', ['ae', 'al', 'au'])
    def test_acknowledgements(self, name):
        """Test the auroral electrojet acknowledgements.

        Parameters
        ----------
        name : str
            Instrument name

        """
        self.out = mm_ae.acknowledgements(name, 'lasp')
        assert self.out.find(name.upper()) >= 0
        return

    @pytest.mark.parametrize('name', ['ae', 'al', 'au'])
    def test_references(self, name):
        """Test the references for an AE instrument.

        Parameters
        ----------
        name : str
            Instrument name

        """
        self.out = mm_ae.references(name, 'lasp')
        assert self.out.find('Davis, T. N.') >= 0
        return
