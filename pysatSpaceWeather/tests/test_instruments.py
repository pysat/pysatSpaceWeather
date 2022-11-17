"""Unit and Integration Tests for each instrument module.

Note
----
Imports test methods from pysat.tests.instrument_test_class

"""

import logging

# Make sure to import your instrument library here
import pysatSpaceWeather

# Import the test classes from pysat
from pysat.tests.classes import cls_instrument_library as clslib


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


class TestSWInstrumentLogging(object):
    """Test logging messages raised under instrument-specific conditions."""

    def setup_method(self):
        """Create a clean the testing setup."""

        self.inst_kwargs = [
            {'inst_module': pysatSpaceWeather.instruments.sw_f107,
             'tag': 'historic'}]

    def teardown_method(self):
        """Clean up previous testing setup."""

        del self.inst_kwargs
        return

    def test_historic_download_past_limit(self, caplog):
        """Test message raised if loading times not in the database."""

        with caplog.at_level(logging.INFO, logger='pysat'):
            inst = pysat.Instrument(**self.inst_kwargs[0])
            inst.download(start=inst.today())

        # Test the warning
        captured = caplog.text
        assert captured.find('date may be out of range for the database.') >= 0

        # Test the file was not downloaded
        assert inst.today() not in inst.files.files.index

        return
