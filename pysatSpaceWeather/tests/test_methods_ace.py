import datetime as dt
import numpy as np

import pandas as pds
import pytest
import pysat

import pysatSpaceWeather as pysat_sw
from pysatSpaceWeather.instruments.methods import ace as mm_ace


class TestACEMethods():
    def setup(self):
        """Runs before every method to create a clean testing setup"""
        self.out = None

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.out

    def test_acknowledgements(self):
        """ Test the ACE acknowledgements """
        self.out = mm_ace.acknowledgements()
        assert self.out.find('ACE') >= 0
        return

    @pytest.mark.parametrize('name', ['mag', 'epam', 'swepam', 'sis'])
    def test_references(self, name):
        """ Test the references for an ACE instrument"""
        self.out = mm_ace.references(name)
        assert self.out.find('Space Sci. Rev.') > 0
        return

    def test_references_bad_name(self):
        """ Test the references raise an informative error for bad instrument
        """
        with pytest.raises(KeyError) as kerr:
            mm_ace.references('ace')

        assert str(kerr.value).find('unknown ACE instrument') >= 0
        return
