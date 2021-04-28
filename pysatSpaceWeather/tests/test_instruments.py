import numpy as np
import tempfile
import warnings

import pytest

# Import the test classes from pysat
import pysat
from pysat.utils import generate_instrument_list
from pysat.tests.instrument_test_class import InstTestClass

# Make sure to import your instrument library here
import pysatSpaceWeather

# Developers for instrument libraries should update the following line to
# point to their own library package
# e.g., instruments = generate_instrument_list(inst_loc=mypackage.instruments)
instruments = generate_instrument_list(inst_loc=pysatSpaceWeather.instruments)

# The following lines apply the custom instrument lists to each type of test
method_list = [func for func in dir(InstTestClass)
               if callable(getattr(InstTestClass, func))]

# Search tests for iteration via pytestmark, update instrument list
for method in method_list:
    if hasattr(getattr(InstTestClass, method), 'pytestmark'):
        # Get list of names of pytestmarks
        Nargs = len(getattr(InstTestClass, method).pytestmark)
        names = [getattr(InstTestClass, method).pytestmark[j].name
                 for j in range(0, Nargs)]
        # Add instruments from your library
        if 'all_inst' in names:
            mark = pytest.mark.parametrize("inst_name", instruments['names'])
            getattr(InstTestClass, method).pytestmark.append(mark)
        elif 'download' in names:
            mark = pytest.mark.parametrize("inst_dict", instruments['download'])
            getattr(InstTestClass, method).pytestmark.append(mark)
        elif 'no_download' in names:
            mark = pytest.mark.parametrize("inst_dict",
                                           instruments['no_download'])
            getattr(InstTestClass, method).pytestmark.append(mark)


class TestInstruments(InstTestClass):
    def setup_class(self):
        """Runs once before the tests to initialize the testing setup."""
        # Make sure to use a temporary directory so that the user's setup is
        # not altered
        self.tempdir = tempfile.TemporaryDirectory()
        self.saved_path = pysat.params['data_dirs']
        pysat.params.data['data_dirs'] = [self.tempdir.name]

        # Developers for instrument libraries should update the following line
        # to point to their own subpackage location, e.g.,
        # self.inst_loc = mypackage.instruments
        self.inst_loc = pysatSpaceWeather.instruments

    def teardown_class(self):
        """Runs after every method to clean up previous testing."""
        pysat.params.data['data_dirs'] = self.saved_path
        self.tempdir.cleanup()
        del self.inst_loc, self.saved_path, self.tempdir

    def setup_method(self):
        """Runs before every method to create a clean testing setup."""

    def teardown_method(self):
        """Runs after every method to clean up previous testing."""


class TestDeprecation():
    def setup(self):
        """Runs before every method to create a clean testing setup"""
        warnings.simplefilter("always", DeprecationWarning)
        self.in_kwargs = {"platform": 'sw', "name": 'f107', "tag": 'all',
                          "inst_id": '', "clean_level": 'clean'}
        self.warn_msgs = ["tag has been deprecated"]

        self.warn_msgs = np.array(self.warn_msgs)

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.in_kwargs, self.warn_msgs

    def eval_warnings(self):
        """Routine to evaluate warnings raised when Instrument instantiated
        """
        # Catch the warnings
        with warnings.catch_warnings(record=True) as war:
            pysat.Instrument(**self.in_kwargs)

        # Ensure the minimum number of warnings were raised
        assert len(war) >= len(self.warn_msgs)

        # Test the warning messages, ensuring each attribute is present
        found_msgs = pysat.instruments.methods.testing.eval_dep_warnings(
            war, self.warn_msgs)

        for i, good in enumerate(found_msgs):
            assert good, "didn't find warning about: {:}".format(
                self.warn_msgs[i])

        return

    def test_deprecated_init(self):
        """Test for deprecated initialization options."""
        # Evaluate warnings
        self.eval_warnings()
        return
