#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
# ----------------------------------------------------------------------------
"""Integration and unit test suite for NoRP methods."""

import pytest

from pysatSpaceWeather.instruments.methods import norp as mm_norp


class TestNoRPMethods(object):
    """Test class for NoRP methods."""

    def setup_method(self):
        """Create a clean testing setup."""
        self.out = None
        return

    def teardown_method(self):
        """Clean up previous testing setup."""
        del self.out
        return

    def test_acknowledgements(self):
        """Test the NoRP acknowledgements."""
        self.out = mm_norp.acknowledgements()
        assert self.out.find('NoRP') >= 0
        return

    @pytest.mark.parametrize('name,tag', [('rf', 'daily')])
    def test_references(self, name, tag):
        """Test the references for a NoRP instrument.

        Parameters
        ----------
        name : str
            Instrument name
        tag : str
            Instrument tag

        """
        self.out = mm_norp.references(name, tag)
        assert self.out.find('Toyokawa Observatory') > 0
        return

    def test_references_bad_name(self):
        """Test the references raise an informative error for bad instrument."""
        with pytest.raises(KeyError) as kerr:
            mm_norp.references('ace', 'sis')

        assert str(kerr.value).find('ace') >= 0, \
            "Unknown KeyError message: {:}".format(kerr.value)
        return
