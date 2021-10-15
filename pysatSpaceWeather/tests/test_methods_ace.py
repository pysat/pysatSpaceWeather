#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
# ----------------------------------------------------------------------------
"""Integration and unit test suite for ACE methods."""

import pytest

from pysatSpaceWeather.instruments.methods import ace as mm_ace


class TestACEMethods(object):
    """Test class for ACE methods."""

    def setup(self):
        """Create a clean testing setup."""
        self.out = None
        return

    def teardown(self):
        """Clean up previous testing setup."""
        del self.out
        return

    def test_acknowledgements(self):
        """Test the ACE acknowledgements."""
        self.out = mm_ace.acknowledgements()
        assert self.out.find('ACE') >= 0
        return

    @pytest.mark.parametrize('name', ['mag', 'epam', 'swepam', 'sis'])
    def test_references(self, name):
        """Test the references for an ACE instrument."""
        self.out = mm_ace.references(name)
        assert self.out.find('Space Sci. Rev.') > 0
        return

    def test_references_bad_name(self):
        """Test the references raise an informative error for bad instrument."""
        with pytest.raises(KeyError) as kerr:
            mm_ace.references('ace')

        assert str(kerr.value).find('unknown ACE instrument') >= 0
        return
