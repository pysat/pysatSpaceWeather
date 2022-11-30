"""Unit and Integration Tests for each instrument module.

Note
----
Imports test methods from pysat.tests.instrument_test_class

"""

import datetime as dt
import logging
import os
import pytest
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


class TestSWInstrumentLogging(object):
    """Test logging messages raised under instrument-specific conditions."""

    def setup_method(self):
        """Create a clean the testing setup."""
        # Prepare for testing downloads
        self.saved_path = pysat.params['data_dirs']
        pysat.params.data['data_dirs'] = [pysatSpaceWeather.test_data_path]
        self.saved_files = list()

        # Assign the Instrument kwargs
        self.inst_kwargs = [
            {'inst_module': pysatSpaceWeather.instruments.sw_f107,
             'tag': 'historic'},
            {'inst_module': pysatSpaceWeather.instruments.sw_kp},
            {'inst_module': pysatSpaceWeather.instruments.ace_epam},
            {'inst_module': pysatSpaceWeather.instruments.sw_f107,
             'tag': 'prelim'}]

    def teardown_method(self):
        """Clean up previous testing setup."""
        # Clean up the pysat parameter space
        pysat.params.data['data_dirs'] = self.saved_path

        for saved_file in self.saved_files:
            attempts = 0
            # Remove file with multiple attempts for Windows
            while os.path.isfile(saved_file) and attempts < 100:
                os.remove(saved_file)
                attempts += 1

            # Remove empty directories
            os.removedirs(os.path.split(saved_file)[0])

        del self.inst_kwargs, self.saved_path, self.saved_files
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

    @pytest.mark.parametrize("tag", ["def", "now"])
    def test_missing_kp_file(self, tag, caplog):
        """Test message raised if loading times not in the database.

        Parameters
        ----------
        tag: str
            Kp Instrument tag

        """
        # Initalize the Instrument and time
        inst = pysat.Instrument(tag=tag, **self.inst_kwargs[1])
        future_time = inst.today() + dt.timedelta(weeks=500)
        cap_text = 'Unable to download'

        # Get the logging message
        with caplog.at_level(logging.INFO, logger='pysat'):
            inst.download(start=future_time)

        # Test the warning
        captured = caplog.text
        assert captured.find(cap_text) >= 0, "Unexpected text: {:}".format(
            captured)

        # Test the file was not downloaded
        assert future_time not in inst.files.files.index
        self.saved_files = [inst.files.data_path,
                            inst.files.data_path.replace('kp', 'ap'),
                            inst.files.data_path.replace('kp', 'cp')]

        return

    def test_realtime_ace_bad_day(self, caplog):
        """Test message raised when downloading old ACE realtime data."""
        inst = pysat.Instrument(tag='realtime', **self.inst_kwargs[2])
        past_time = inst.today() - dt.timedelta(weeks=500)

        # Get the logging message
        with caplog.at_level(logging.WARNING, logger='pysat'):
            inst.download(start=past_time)

        # Test the warning
        captured = caplog.text
        assert captured.find(
            'real-time data only') >= 0, "Unexpected text: {:}".format(captured)

        # Test the file was downloaded
        assert past_time in inst.files.files.index
        self.saved_files = [os.path.join(inst.files.data_path,
                                         inst.files.files[past_time])]

        return

    def test_historic_ace_no_data(self, caplog):
        """Test message raised when no historic ACE data found on server."""
        inst = pysat.Instrument(tag='historic', **self.inst_kwargs[2])
        past_time = dt.datetime(1800, 1, 1)  # Pre-space age date

        # Get the logging message
        with caplog.at_level(logging.WARNING, logger='pysat'):
            inst.download(start=past_time)

        # Test the warning
        captured = caplog.text
        assert captured.find(
            'not found on server') >= 0, "Unexpected text: {:}".format(captured)

        # Test the file was not downloaded
        assert past_time not in inst.files.files.index
        self.saved_files = [inst.files.data_path]

        return

    def test_missing_prelim_file(self, caplog):
        """Test message raised if loading times not in the DSD database."""
        # Initalize the Instrument, time, and expected log output
        inst = pysat.Instrument(**self.inst_kwargs[3])
        future_time = inst.today() + dt.timedelta(weeks=500)
        cap_text = 'File not available for'

        # Get the logging message
        with caplog.at_level(logging.INFO, logger='pysat'):
            inst.download(start=future_time)

        # Test the warning
        captured = caplog.text
        assert captured.find(cap_text) >= 0, "Unexpected text: {:}".format(
            captured)

        # Test the file was not downloaded
        assert future_time not in inst.files.files.index
        self.saved_files = [inst.files.data_path,
                            inst.files.data_path.replace('f107', 'sbfield'),
                            inst.files.data_path.replace('f107', 'ssn'),
                            inst.files.data_path.replace('f107', 'flare')]

        return
