import datetime as dt
import numpy as np

import pandas as pds
import pytest
import pysat

import pysatSpaceWeather as pysat_sw
from pysatSpaceWeather.instruments import sw_f107
from pysatSpaceWeather.instruments.methods import f107 as mm_f107


class TestSWF107():
    def setup(self):
        """Runs before every method to create a clean testing setup"""
        # Load a test instrument
        self.testInst = pysat.Instrument()
        self.testInst.data = pds.DataFrame({'f107': np.linspace(70, 200, 160)},
                                           index=[dt.datetime(2009, 1, 1)
                                                  + pds.DateOffset(days=i)
                                                  for i in range(160)])

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst

    def test_calc_f107a_bad_inname(self):
        """ Test the calc_f107a with a bad input name """

        with pytest.raises(ValueError):
            sw_f107.calc_f107a(self.testInst, 'bad')

    def test_calc_f107a_bad_outname(self):
        """ Test the calc_f107a with a bad output name """

        with pytest.raises(ValueError):
            sw_f107.calc_f107a(self.testInst, 'f107', 'f107')

    def test_calc_f107a_daily(self):
        """ Test the calc_f107a routine with daily data"""

        sw_f107.calc_f107a(self.testInst, f107_name='f107', f107a_name='f107a')

        # Assert that new data and metadata exist
        assert 'f107a' in self.testInst.data.columns
        assert 'f107a' in self.testInst.meta.keys()

        # Assert the values are finite and realistic means
        assert np.all(np.isfinite(self.testInst['f107a']))
        assert self.testInst['f107a'].min() > self.testInst['f107'].min()
        assert self.testInst['f107a'].max() < self.testInst['f107'].max()

    def test_calc_f107a_high_rate(self):
        """ Test the calc_f107a routine with sub-daily data"""
        self.testInst.data = pds.DataFrame({'f107': np.linspace(70, 200,
                                                                3840)},
                                           index=[dt.datetime(2009, 1, 1)
                                                  + pds.DateOffset(hours=i)
                                                  for i in range(3840)])
        sw_f107.calc_f107a(self.testInst, f107_name='f107', f107a_name='f107a')

        # Assert that new data and metadata exist
        assert 'f107a' in self.testInst.data.columns
        assert 'f107a' in self.testInst.meta.keys()

        # Assert the values are finite and realistic means
        assert np.all(np.isfinite(self.testInst['f107a']))
        assert self.testInst['f107a'].min() > self.testInst['f107'].min()
        assert self.testInst['f107a'].max() < self.testInst['f107'].max()

        # Assert the same mean value is used for a day
        assert len(np.unique(self.testInst['f107a'][:24])) == 1

    def test_calc_f107a_daily_missing(self):
        """ Test the calc_f107a routine with some daily data missing"""

        self.testInst.data = pds.DataFrame({'f107': np.linspace(70, 200, 160)},
                                           index=[dt.datetime(2009, 1, 1)
                                                  + pds.DateOffset(days=(2 * i
                                                                         + 1))
                                                  for i in range(160)])
        sw_f107.calc_f107a(self.testInst, f107_name='f107', f107a_name='f107a')

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


class TestSWF107Combine():
    def setup(self):
        """Runs before every method to create a clean testing setup"""
        # Switch to test_data directory
        self.saved_path = pysat.data_dir
        pysat.utils.set_data_dir(pysat_sw.test_data_path, store=False)

        # Set combination testing input
        self.test_day = dt.datetime(2019, 3, 16)
        self.combineInst = {tag: pysat.Instrument(inst_module=sw_f107, tag=tag,
                                                  update_files=True)
                            for tag in sw_f107.tags.keys()}
        self.combineTimes = {"start": self.test_day - dt.timedelta(days=30),
                             "stop": self.test_day + dt.timedelta(days=3)}

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        pysat.utils.set_data_dir(self.saved_path)
        del self.combineInst, self.test_day, self.combineTimes

    def test_combine_f107_none(self):
        """ Test combine_f107 failure when no input is provided"""

        with pytest.raises(TypeError):
            mm_f107.combine_f107()

    def test_combine_f107_no_time(self):
        """Test combine_f107 failure when no times are provided"""

        with pytest.raises(ValueError):
            mm_f107.combine_f107(self.combineInst[''],
                                 self.combineInst['forecast'])

    def test_combine_f107_no_data(self):
        """Test combine_f107 when no data is present for specified times"""

        combo_in = {kk: self.combineInst['forecast'] for kk in
                    ['standard_inst', 'forecast_inst']}
        combo_in['start'] = dt.datetime(2014, 2, 19)
        combo_in['stop'] = dt.datetime(2014, 2, 24)
        f107_inst = mm_f107.combine_f107(**combo_in)

        assert f107_inst.data.isnull().all()["f107"]

        del combo_in, f107_inst

    def test_combine_f107_inst_time(self):
        """Test combine_f107 with times provided through datasets"""

        self.combineInst['all'].load(date=self.combineTimes['start'])
        self.combineInst['forecast'].load(date=self.test_day)

        f107_inst = mm_f107.combine_f107(self.combineInst['all'],
                                         self.combineInst['forecast'])

        assert f107_inst.index[0] == dt.datetime(1947, 2, 13)
        assert f107_inst.index[-1] <= self.combineTimes['stop']
        assert len(f107_inst.data.columns) == 1
        assert f107_inst.data.columns[0] == 'f107'

        del f107_inst

    def test_combine_f107_all(self):
        """Test combine_f107 when all input is provided with '' and '45day'"""

        f107_inst = mm_f107.combine_f107(self.combineInst[''],
                                         self.combineInst['45day'],
                                         **self.combineTimes)

        assert f107_inst.index[0] >= self.combineTimes['start']
        assert f107_inst.index[-1] < self.combineTimes['stop']
        assert len(f107_inst.data.columns) == 1
        assert f107_inst.data.columns[0] == 'f107'

        del f107_inst
