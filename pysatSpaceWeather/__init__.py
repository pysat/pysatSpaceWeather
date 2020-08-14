import os

from pysatSpaceWeather import instruments  # noqa F401

# Set directory for test data
here = os.path.abspath(os.path.dirname(__file__))
test_data_path = os.path.join(here, 'tests', 'test_data')
