#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
# ----------------------------------------------------------------------------
"""Test suite for F10.7 methods."""

import datetime as dt
import numpy as np
from packaging.version import Version

import pandas as pds
import pysat
import pytest

import pysatSpaceWeather as pysat_sw
from pysatSpaceWeather.instruments.methods import f107 as mm_f107
from pysatSpaceWeather.instruments import sw_f107


class TestSWF107(object):
    """Test class for F10.7 methods."""

    def setup(self):
        """Create a clean testing setup."""
        # Load a test instrument
        self.testInst = pysat.Instrument()
        self.testInst.data = pds.DataFrame({'f107': np.linspace(70, 200, 160)},
                                           index=[dt.datetime(2009, 1, 1)
                                                  + pds.DateOffset(days=i)
                                                  for i in range(160)])
        return

    def teardown(self):
        """Clean up previous testing setup."""
        del self.testInst
        return

    @pytest.mark.parametrize("inargs,vmsg", [
        (["bad"], "unknown input data column"),
        (['f107', 'f107'], "output data column already exists")])
    def test_calc_f107a_bad_inputs(self, inargs, vmsg):
        """Test the calc_f107a with a bad inputs.

        Parameters
        ----------
        inargs : list
            List of input arguements that should raise a ValueError
        vmsg : str
            Expected ValueError message

        """

        with pytest.raises(ValueError) as verr:
            mm_f107.calc_f107a(self.testInst, *inargs)

        assert str(verr).find(vmsg) >= 0
        return

    def test_calc_f107a_daily(self):
        """Test the calc_f107a routine with daily data."""

        mm_f107.calc_f107a(self.testInst, f107_name='f107', f107a_name='f107a')

        # Assert that new data and metadata exist
        assert 'f107a' in self.testInst.data.columns
        assert 'f107a' in self.testInst.meta.keys()

        # Assert the values are finite and realistic means
        assert np.all(np.isfinite(self.testInst['f107a']))
        assert self.testInst['f107a'].min() > self.testInst['f107'].min()
        assert self.testInst['f107a'].max() < self.testInst['f107'].max()
        return

    def test_calc_f107a_high_rate(self):
        """Test the calc_f107a routine with sub-daily data."""
        self.testInst.data = pds.DataFrame({'f107': np.linspace(70, 200,
                                                                3840)},
                                           index=[dt.datetime(2009, 1, 1)
                                                  + pds.DateOffset(hours=i)
                                                  for i in range(3840)])
        mm_f107.calc_f107a(self.testInst, f107_name='f107', f107a_name='f107a')

        # Assert that new data and metadata exist
        assert 'f107a' in self.testInst.data.columns
        assert 'f107a' in self.testInst.meta.keys()

        # Assert the values are finite and realistic means
        assert np.all(np.isfinite(self.testInst['f107a']))
        assert self.testInst['f107a'].min() > self.testInst['f107'].min()
        assert self.testInst['f107a'].max() < self.testInst['f107'].max()

        # Assert the same mean value is used for a day
        assert len(np.unique(self.testInst['f107a'][:24])) == 1
        return

    def test_calc_f107a_daily_missing(self):
        """Test the calc_f107a routine with some daily data missing."""

        self.testInst.data = pds.DataFrame({'f107': np.linspace(70, 200, 160)},
                                           index=[dt.datetime(2009, 1, 1)
                                                  + pds.DateOffset(days=(2 * i
                                                                         + 1))
                                                  for i in range(160)])
        mm_f107.calc_f107a(self.testInst, f107_name='f107', f107a_name='f107a')

        # Assert that new data and metadata exist
        assert 'f107a' in self.testInst.data.columns
        assert 'f107a' in self.testInst.meta.keys()

        # Assert the finite values have realistic means
        assert(np.nanmin(self.testInst['f107a'])
               > np.nanmin(self.testInst['f107']))
        assert(np.nanmax(self.testInst['f107a'])
               < np.nanmax(self.testInst['f107']))

        # Assert the expected number of fill values
        assert(len(self.testInst['f107a'][np.isnan(self.testInst['f107a'])])
               == 40)
        return


class TestSWF107Combine(object):
    """Test class for the `combine_f107` method."""

    def setup(self):
        """Create a clean testing setup."""
        # Switch to test_data directory
        self.saved_path = pysat.params['data_dirs']
        pysat.params.data['data_dirs'] = [pysat_sw.test_data_path]

        # Set combination testing input
        self.test_day = dt.datetime(2019, 3, 16)
        self.combine_inst = {tag: pysat.Instrument(inst_module=sw_f107, tag=tag,
                                                   update_files=True)
                             for tag in sw_f107.tags.keys()}
        self.combine_times = {"start": self.test_day - dt.timedelta(days=30),
                              "stop": self.test_day + dt.timedelta(days=3)}
        self.load_kwargs = {}
        if Version(pysat.__version__) > Version('3.0.1'):
            self.load_kwargs['use_header'] = True

        return

    def teardown(self):
        """Clean up previous testing setup."""
        pysat.params.data['data_dirs'] = self.saved_path
        del self.combine_inst, self.test_day, self.combine_times
        del self.load_kwargs
        return

    def test_combine_f107_none(self):
        """Test `combine_f107` failure when no input is provided."""

        with pytest.raises(TypeError) as terr:
            mm_f107.combine_f107()

        assert str(terr).find("missing 2 required positional arguments") >= 0
        return

    def test_combine_f107_no_time(self):
        """Test `combine_f107` failure when no times are provided."""

        with pytest.raises(ValueError) as verr:
            mm_f107.combine_f107(self.combine_inst['historic'],
                                 self.combine_inst['forecast'])

        assert str(verr).find("must either load in Instrument objects") >= 0
        return

    def test_combine_f107_bad_time(self):
        """Test `combine_f107` failure when bad times are provided."""

        with pytest.raises(ValueError) as verr:
            mm_f107.combine_f107(self.combine_inst['historic'],
                                 self.combine_inst['forecast'],
                                 start=self.combine_times['stop'],
                                 stop=self.combine_times['start'])

        assert str(verr).find("date range is zero or negative") >= 0
        return

    def test_combine_f107_no_data(self):
        """Test `combine_f107` when no data is present for specified times."""

        combo_in = {kk: self.combine_inst['forecast'] for kk in
                    ['standard_inst', 'forecast_inst']}
        combo_in['start'] = dt.datetime(2014, 2, 19)
        combo_in['stop'] = dt.datetime(2014, 2, 24)
        f107_inst = mm_f107.combine_f107(**combo_in)

        assert f107_inst.data.isnull().all()["f107"]

        del combo_in, f107_inst
        return

    def test_combine_f107_inst_time(self):
        """Test `combine_f107` with times provided through datasets."""

        self.combine_inst['historic'].load(
            date=self.combine_inst['historic'].lasp_stime,
            end_date=self.combine_times['start'], **self.load_kwargs)
        self.combine_inst['forecast'].load(date=self.test_day,
                                           **self.load_kwargs)

        f107_inst = mm_f107.combine_f107(self.combine_inst['historic'],
                                         self.combine_inst['forecast'])

        assert f107_inst.index[0] == self.combine_inst['historic'].lasp_stime
        assert f107_inst.index[-1] <= self.combine_times['stop']
        assert len(f107_inst.data.columns) == 1
        assert f107_inst.data.columns[0] == 'f107'

        del f107_inst
        return

    def test_combine_f107_all(self):
        """Test `combine_f107` with 'historic' and '45day' input."""

        f107_inst = mm_f107.combine_f107(self.combine_inst['historic'],
                                         self.combine_inst['45day'],
                                         **self.combine_times)

        assert f107_inst.index[0] >= self.combine_times['start']
        assert f107_inst.index[-1] < self.combine_times['stop']
        assert len(f107_inst.data.columns) == 1
        assert f107_inst.data.columns[0] == 'f107'

        del f107_inst
        return
