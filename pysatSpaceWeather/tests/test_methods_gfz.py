#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
#
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
"""Integration and unit test suite for ACE methods."""

import datetime as dt
import pytest
import tempfile

import pysat

from pysatSpaceWeather.instruments.methods import gfz


class TestGFZMethods(object):
    """Test class for ACE methods."""

    def setup_method(self):
        """Create a clean testing setup."""
        # Prepare for testing downloads
        self.tempdir = tempfile.TemporaryDirectory()
        self.saved_path = pysat.params['data_dirs']
        pysat.params._set_data_dirs(path=self.tempdir.name, store=False)
        return

    def teardown_method(self):
        """Clean up previous testing setup."""
        # Clean up the pysat parameter space
        pysat.params._set_data_dirs(self.saved_path, store=False)

        del self.tempdir, self.saved_path
        return

    def test_kp_ap_cp_download_bad_inst(self):
        """Test the download doesn't work for an incorrect Instrument."""
        with pytest.raises(ValueError) as verr:
            gfz.kp_ap_cp_download('platform', 'name', 'tag', 'inst_id',
                                  [dt.datetime.now(tz=dt.timezone.utc)],
                                  'data/path')

        assert str(verr).find('Unknown Instrument module') >= 0
        return
