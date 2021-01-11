#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
# ----------------------------------------------------------------------------

import datetime as dt
import numpy as np

import pandas as pds
import pytest
import pysat

import pysatSpaceWeather as pysat_sw
from pysatSpaceWeather.instruments import sw_kp
from pysatSpaceWeather.instruments.methods import kp_ap


class TestSWKp():
    def setup(self):
        """Runs before every method to create a clean testing setup"""
        # Load a test instrument
        self.testInst = pysat.Instrument()
        self.testInst.data = \
            pds.DataFrame({'Kp': np.arange(0, 4, 1.0 / 3.0),
                           'ap_nan': np.full(shape=12, fill_value=np.nan),
                           'ap_inf': np.full(shape=12, fill_value=np.inf)},
                          index=[dt.datetime(2009, 1, 1)
                                 + pds.DateOffset(hours=3 * i)
                                 for i in range(12)])
        self.testInst.meta = pysat.Meta()
        self.testInst.meta['Kp'] = {self.testInst.meta.labels.fill_val: np.nan}
        self.testInst.meta['ap_nan'] = {self.testInst.meta.labels.fill_val:
                                        np.nan}
        self.testInst.meta['ap_inf'] = {self.testInst.meta.labels.fill_val:
                                        np.inf}

        # Load a test Metadata
        self.testMeta = pysat.Meta()

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.testMeta

    def test_convert_kp_to_ap(self):
        """ Test conversion of Kp to ap"""

        kp_ap.convert_3hr_kp_to_ap(self.testInst)

        assert '3hr_ap' in self.testInst.data.columns
        assert '3hr_ap' in self.testInst.meta.keys()
        assert self.testInst['3hr_ap'].min() >= self.testInst.meta[
            '3hr_ap'][self.testInst.meta.labels.min_val]
        assert self.testInst['3hr_ap'].max() <= self.testInst.meta[
            '3hr_ap'][self.testInst.meta.labels.max_val]

    def test_convert_kp_to_ap_fill_val(self):
        """ Test conversion of Kp to ap with fill values"""

        # Set the first value to a fill value, then calculate ap
        fill_val = self.testInst.meta.labels.fill_val
        self.testInst['Kp'][0] = self.testInst.meta['Kp'][fill_val]
        kp_ap.convert_3hr_kp_to_ap(self.testInst)

        # Test non-fill ap values
        assert '3hr_ap' in self.testInst.data.columns
        assert '3hr_ap' in self.testInst.meta.keys()
        assert self.testInst['3hr_ap'][1:].min() >= self.testInst.meta[
            '3hr_ap'][self.testInst.meta.labels.min_val]
        assert self.testInst['3hr_ap'][1:].max() <= self.testInst.meta[
            '3hr_ap'][self.testInst.meta.labels.max_val]

        # Test the fill value in the data and metadata
        assert np.isnan(self.testInst['3hr_ap'][0])
        assert np.isnan(self.testInst.meta['3hr_ap'][fill_val])

        del fill_val

    def test_convert_kp_to_ap_bad_input(self):
        """ Test conversion of Kp to ap with bad input"""

        self.testInst.data.rename(columns={"Kp": "bad"}, inplace=True)

        with pytest.raises(ValueError):
            kp_ap.convert_3hr_kp_to_ap(self.testInst)

    def test_initialize_kp_metadata(self):
        """Test default Kp metadata initialization"""
        kp_ap.initialize_kp_metadata(self.testInst.meta, 'Kp')

        assert self.testInst.meta['Kp'][self.testInst.meta.labels.units] == ''
        assert self.testInst.meta['Kp'][self.testInst.meta.labels.name] == 'Kp'
        assert self.testInst.meta['Kp'][
            self.testInst.meta.labels.desc] == 'Planetary K-index'
        assert self.testInst.meta['Kp'][self.testInst.meta.labels.min_val] == 0
        assert self.testInst.meta['Kp'][self.testInst.meta.labels.max_val] == 9
        assert self.testInst.meta['Kp'][
            self.testInst.meta.labels.fill_val] == -1

    def test_uninit_kp_metadata(self):
        """Test Kp metadata initialization with uninitialized Metadata"""
        kp_ap.initialize_kp_metadata(self.testMeta, 'Kp')

        assert self.testMeta['Kp'][self.testMeta.labels.units] == ''
        assert self.testMeta['Kp'][self.testMeta.labels.name] == 'Kp'
        assert(self.testMeta['Kp'][self.testMeta.labels.desc]
               == 'Planetary K-index')
        assert self.testMeta['Kp'][self.testMeta.labels.min_val] == 0
        assert self.testMeta['Kp'][self.testMeta.labels.max_val] == 9
        assert self.testMeta['Kp'][self.testMeta.labels.fill_val] == -1

    def test_fill_kp_metadata(self):
        """Test Kp metadata initialization with user-specified fill value"""
        kp_ap.initialize_kp_metadata(self.testInst.meta, 'Kp', fill_val=666)

        assert self.testInst.meta['Kp'][
            self.testInst.meta.labels.fill_val] == 666

    def test_long_name_kp_metadata(self):
        """Test Kp metadata initialization with a long name"""
        dkey = 'high_lat_Kp'
        kp_ap.initialize_kp_metadata(self.testInst.meta, dkey)

        assert self.testInst.meta[dkey][self.testInst.meta.labels.name] == dkey
        assert(self.testInst.meta[dkey][self.testInst.meta.labels.desc]
               == 'Planetary K-index')
        del dkey

    def test_convert_ap_to_kp(self):
        """ Test conversion of ap to Kp"""

        kp_ap.convert_3hr_kp_to_ap(self.testInst)
        kp_out, kp_meta = kp_ap.convert_ap_to_kp(self.testInst['3hr_ap'])

        # Assert original and coverted there and back Kp are equal
        assert all(abs(kp_out - self.testInst.data['Kp']) < 1.0e-4)

        # Assert the converted Kp meta data exists and is reasonable
        assert 'Kp' in kp_meta.keys()
        assert kp_meta['Kp'][kp_meta.labels.fill_val] == -1

        del kp_out, kp_meta

    def test_convert_ap_to_kp_middle(self):
        """ Test conversion of ap to Kp where ap is not an exact Kp value"""

        kp_ap.convert_3hr_kp_to_ap(self.testInst)
        self.testInst['3hr_ap'][8] += 1
        kp_out, kp_meta = kp_ap.convert_ap_to_kp(self.testInst['3hr_ap'])

        # Assert original and coverted there and back Kp are equal
        assert all(abs(kp_out - self.testInst.data['Kp']) < 1.0e-4)

        # Assert the converted Kp meta data exists and is reasonable
        assert 'Kp' in kp_meta.keys()
        assert(kp_meta['Kp'][kp_meta.labels.fill_val] == -1)

        del kp_out, kp_meta

    def test_convert_ap_to_kp_nan_input(self):
        """ Test conversion of ap to Kp where ap is NaN"""

        kp_out, kp_meta = kp_ap.convert_ap_to_kp(self.testInst['ap_nan'])

        # Assert original and coverted there and back Kp are equal
        assert all(kp_out == -1)

        # Assert the converted Kp meta data exists and is reasonable
        assert 'Kp' in kp_meta.keys()
        assert(kp_meta['Kp'][kp_meta.labels.fill_val] == -1)

        del kp_out, kp_meta

    def test_convert_ap_to_kp_inf_input(self):
        """ Test conversion of ap to Kp where ap is Inf"""

        kp_out, kp_meta = kp_ap.convert_ap_to_kp(self.testInst['ap_inf'])

        # Assert original and coverted there and back Kp are equal
        assert all(kp_out[1:] == -1)

        # Assert the converted Kp meta data exists and is reasonable
        assert 'Kp' in kp_meta.keys()
        assert(kp_meta['Kp'][kp_meta.labels.fill_val] == -1)

        del kp_out, kp_meta

    def test_convert_ap_to_kp_fill_val(self):
        """ Test conversion of ap to Kp with fill values"""

        # Set the first Kp value to a fill value
        fill_val = self.testInst.meta.labels.fill_val
        self.testInst['Kp'][0] = self.testInst.meta['Kp', fill_val]

        # Calculate ap
        kp_ap.convert_3hr_kp_to_ap(self.testInst)

        # Recalculate Kp from ap
        kp_out, kp_meta = kp_ap.convert_ap_to_kp(
            self.testInst['3hr_ap'],
            fill_val=self.testInst.meta['Kp', fill_val])

        # Test non-fill ap values
        assert all(abs(kp_out[1:] - self.testInst.data['Kp'][1:]) < 1.0e-4)

        # Test the fill value in the data and metadata
        assert np.isnan(kp_out[0])
        assert np.isnan(kp_meta['Kp'][fill_val])

        del fill_val, kp_out, kp_meta


class TestSwKpCombine():
    def setup(self):
        """Runs before every method to create a clean testing setup"""
        # Switch to test_data directory
        self.saved_path = pysat.data_dir
        pysat.utils.set_data_dir(pysat_sw.test_data_path, store=False)

        # Set combination testing input
        self.test_day = dt.datetime(2019, 3, 18)
        self.combine = {"standard_inst": pysat.Instrument(inst_module=sw_kp,
                                                          tag="",
                                                          update_files=True),
                        "recent_inst": pysat.Instrument(inst_module=sw_kp,
                                                        tag="recent",
                                                        update_files=True),
                        "forecast_inst":
                        pysat.Instrument(inst_module=sw_kp,
                                         tag="forecast", update_files=True),
                        "start": self.test_day - dt.timedelta(days=30),
                        "stop": self.test_day + dt.timedelta(days=3),
                        "fill_val": -1}

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        pysat.utils.set_data_dir(self.saved_path)
        del self.combine, self.test_day, self.saved_path

    def test_combine_kp_none(self):
        """ Test combine_kp failure when no input is provided"""

        with pytest.raises(ValueError):
            kp_ap.combine_kp()

    def test_combine_kp_one(self):
        """ Test combine_kp failure when only one instrument is provided"""

        # Load a test instrument
        testInst = pysat.Instrument()
        testInst.data = pds.DataFrame({'Kp': np.arange(0, 4, 1.0 / 3.0)},
                                      index=[dt.datetime(2009, 1, 1)
                                             + pds.DateOffset(hours=3 * i)
                                             for i in range(12)])
        testInst.meta = pysat.Meta()
        testInst.meta['Kp'] = {testInst.meta.labels.fill_val: np.nan}

        combo_in = {"standard_inst": testInst}
        with pytest.raises(ValueError):
            kp_ap.combine_kp(combo_in)

        del combo_in, testInst

    def test_combine_kp_no_time(self):
        """Test combine_kp failure when no times are provided"""

        combo_in = {kk: self.combine[kk] for kk in
                    ['standard_inst', 'recent_inst', 'forecast_inst']}

        with pytest.raises(ValueError):
            kp_ap.combine_kp(combo_in)

        del combo_in

    def test_combine_kp_no_data(self):
        """Test combine_kp when no data is present for specified times"""

        combo_in = {kk: self.combine['forecast_inst'] for kk in
                    ['standard_inst', 'recent_inst', 'forecast_inst']}
        combo_in['start'] = dt.datetime(2014, 2, 19)
        combo_in['stop'] = dt.datetime(2014, 2, 24)
        kp_inst = kp_ap.combine_kp(**combo_in)

        assert kp_inst.data.isnull().all()["Kp"]

        del combo_in, kp_inst

    def test_combine_kp_inst_time(self):
        """Test combine_kp when times are provided through the instruments"""

        combo_in = {kk: self.combine[kk] for kk in
                    ['standard_inst', 'recent_inst', 'forecast_inst']}

        combo_in['standard_inst'].load(date=self.combine['start'])
        combo_in['recent_inst'].load(date=self.test_day)
        combo_in['forecast_inst'].load(date=self.test_day)
        combo_in['stop'] = combo_in['forecast_inst'].index[-1]

        kp_inst = kp_ap.combine_kp(**combo_in)

        assert kp_inst.index[0] >= self.combine['start']
        # kp_inst contains times up to 21:00:00, coombine['stop'] is midnight
        assert kp_inst.index[-1].date() <= self.combine['stop'].date()
        assert len(kp_inst.data.columns) == 1
        assert kp_inst.data.columns[0] == 'Kp'

        assert np.isnan(kp_inst.meta['Kp'][kp_inst.meta.labels.fill_val])
        assert len(kp_inst['Kp'][np.isnan(kp_inst['Kp'])]) == 0

        del combo_in, kp_inst

    def test_combine_kp_all(self):
        """Test combine_kp when all input is provided"""

        kp_inst = kp_ap.combine_kp(**self.combine)

        assert kp_inst.index[0] >= self.combine['start']
        assert kp_inst.index[-1] < self.combine['stop']
        assert len(kp_inst.data.columns) == 1
        assert kp_inst.data.columns[0] == 'Kp'

        # Fill value is defined by combine
        assert(kp_inst.meta['Kp'][kp_inst.meta.labels.fill_val]
               == self.combine['fill_val'])
        assert (kp_inst['Kp'] != self.combine['fill_val']).all()

        del kp_inst

    def test_combine_kp_no_forecast(self):
        """Test combine_kp when forecasted data is not provided"""

        combo_in = {kk: self.combine[kk] for kk in self.combine.keys()
                    if kk != 'forecast_inst'}
        kp_inst = kp_ap.combine_kp(**combo_in)

        assert kp_inst.index[0] >= self.combine['start']
        assert kp_inst.index[-1] < self.combine['stop']
        assert len(kp_inst.data.columns) == 1
        assert kp_inst.data.columns[0] == 'Kp'
        assert(kp_inst.meta['Kp'][kp_inst.meta.labels.fill_val]
               == self.combine['fill_val'])
        assert (kp_inst['Kp'] == self.combine['fill_val']).any()

        del kp_inst, combo_in

    def test_combine_kp_no_recent(self):
        """Test combine_kp when recent data is not provided"""

        combo_in = {kk: self.combine[kk] for kk in self.combine.keys()
                    if kk != 'recent_inst'}
        kp_inst = kp_ap.combine_kp(**combo_in)

        assert kp_inst.index[0] >= self.combine['start']
        assert kp_inst.index[-1] < self.combine['stop']
        assert len(kp_inst.data.columns) == 1
        assert kp_inst.data.columns[0] == 'Kp'
        assert (kp_inst.meta['Kp'][kp_inst.meta.labels.fill_val]
                == self.combine['fill_val'])
        assert (kp_inst['Kp'] == self.combine['fill_val']).any()

        del kp_inst, combo_in

    def test_combine_kp_no_standard(self):
        """Test combine_kp when standard data is not provided"""

        combo_in = {kk: self.combine[kk] for kk in self.combine.keys()
                    if kk != 'standard_inst'}
        kp_inst = kp_ap.combine_kp(**combo_in)

        assert kp_inst.index[0] >= self.combine['start']
        assert kp_inst.index[-1] < self.combine['stop']
        assert len(kp_inst.data.columns) == 1
        assert kp_inst.data.columns[0] == 'Kp'
        assert(kp_inst.meta['Kp'][kp_inst.meta.labels.fill_val]
               == self.combine['fill_val'])
        assert len(kp_inst['Kp'][kp_inst['Kp']]
                   == self.combine['fill_val']) > 0

        del kp_inst, combo_in


class TestSWAp():
    def setup(self):
        """Runs before every method to create a clean testing setup"""
        # Load a test instrument with 3hr ap data
        self.testInst = pysat.Instrument()
        self.testInst.data = pds.DataFrame({'3hr_ap': [0, 2, 3, 4, 5, 6, 7, 9,
                                                       12, 15]},
                                           index=[dt.datetime(2009, 1, 1)
                                                  + pds.DateOffset(hours=3 * i)
                                                  for i in range(10)])
        self.testInst.meta = pysat.Meta()
        self.meta_dict = {self.testInst.meta.labels.units: '',
                          self.testInst.meta.labels.name: 'ap',
                          self.testInst.meta.labels.desc:
                          "3-hour ap (equivalent range) index",
                          self.testInst.meta.labels.min_val: 0,
                          self.testInst.meta.labels.max_val: 400,
                          self.testInst.meta.labels.fill_val: np.nan,
                          self.testInst.meta.labels.notes: 'test ap'}
        self.testInst.meta['3hr_ap'] = self.meta_dict

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.meta_dict

    def test_calc_daily_Ap(self):
        """ Test daily Ap calculation"""

        kp_ap.calc_daily_Ap(self.testInst)

        assert 'Ap' in self.testInst.data.columns
        assert 'Ap' in self.testInst.meta.keys()

        # Test unfilled values (full days)
        assert np.all(self.testInst['Ap'][:8].min() == 4.5)

        # Test fill values (partial days)
        assert np.all(np.isnan(self.testInst['Ap'][8:]))

    def test_calc_daily_Ap_bad_3hr(self):
        """ Test daily Ap calculation with bad input key"""

        with pytest.raises(ValueError):
            kp_ap.calc_daily_Ap(self.testInst, "no")

    def test_calc_daily_Ap_bad_daily(self):
        """ Test daily Ap calculation with bad output key"""

        with pytest.raises(ValueError):
            kp_ap.calc_daily_Ap(self.testInst, "3hr_ap", "3hr_ap")
