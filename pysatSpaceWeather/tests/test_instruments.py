"""Unit and Integration Tests for each instrument module.

Note
----
Imports test methods from pysat.tests.instrument_test_class

"""

import datetime as dt
import logging
import warnings

# Make sure to import your instrument library here
import pysatSpaceWeather

# Import the test classes from pysat
import pysat
from pysat.tests.classes import cls_instrument_library as clslib
from pysat.utils import testing


# Tell the standard tests which instruments to run each test on.
# Need to return instrument list for custom tests.
instruments = clslib.InstLibTests.initialize_test_package(
    clslib.InstLibTests, inst_loc=pysatSpaceWeather.instruments)


class TestInstruments(clslib.InstLibTests):
    """Main class for instrument tests.

    Note
    ----
    All standard tests, setup, and teardown inherited from the core pysat
    instrument test class.

    """


class TestLocalDeprecation(object):
    """Unit tests for local instrument deprecation warnings."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        warnings.simplefilter("always", DeprecationWarning)
        self.in_kwargs = {"inst_module": pysatSpaceWeather.instruments.sw_kp,
                          'tag': ''}
        self.ref_time = dt.datetime(2001, 1, 1)
        self.warn_msgs = []
        self.war = ""
        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""

        del self.in_kwargs, self.ref_time, self.warn_msgs, self.war
        return

    def eval_warnings(self):
        """Evaluate the number and message of the raised warnings."""

        # Ensure the minimum number of warnings were raised.
        assert len(self.war) >= len(self.warn_msgs)

        # Test the warning messages, ensuring each attribute is present.
        testing.eval_warnings(self.war, self.warn_msgs)
        return

    def test_sw_kp_default_tag_deprecation(self):
        """Test the deprecation of the '' tag for the sw_kp Instrument."""

        with warnings.catch_warnings(record=True) as self.war:
            pysat.Instrument(**self.in_kwargs)

        self.warn_msgs = ["".join(["Changes at the GFZ database have led to ",
                                   "this data type being deprecated. Switch ",
                                   "to using 'def' for definitive Kp or ",
                                   "'now' for Kp nowcasts from GFZ."])]

        # Evaluate the warning output
        self.eval_warnings()
        return
