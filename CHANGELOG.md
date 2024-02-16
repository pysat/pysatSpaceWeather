Change Log
==========
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](https://semver.org/).

[0.1.0] - 2024-02-16
--------------------
* Enhancements
  * Changed downloads to write files across multiple Instruments when the
    remote files contain a mix of data products
  * Added new instruments: sw_ae, sw_al, sw_au, sw_ap, sw_apo, sw_cp, sw_flare,
    sw_hpo, sw_polar-cap, sw_sbfield, sw_ssn, and sw_storm-prob
  * Added new data sources (tag 'now') for the F10.7 from GFZ
  * Created a general download routine for the GFZ and LASP data
  * Added new examples to the documentation
  * Added new test attributes for clean messages to the ACE instruments
  * Added the ability to 'download' files from a local directory
  * Added an acknowledgements file with detailed funding information
* Maintenance
  * Updated package documentation, yamls, and other supporting files
  * Updated the LISIRD download routine to reflect new behaviour
  * Changed F10.7 daily test day to ensure new pysat padding tests work
  * Removed try/except loop that was a fix for pysat < 3.1.0
  * Updated 'use_header' kwarg use for pysat 3.2.0 changes
  * Updated code headers to include license, reference, and pub release info
  * Updated the supported python versions

[0.0.10] - 2023-06-01
---------------------
* Maintenance
  * Bumped the NEP29 numpy version in tests
  * Updated the docstring, updated the default Kp instrument, and added an
    error catch for empty Instruments in the
    `instruments.methods.kp_ap.filter_geomag` function
  * Updated GitHub Action workflow installs
* Bugs
  * Fixed a bug evaluating the length of preliminary F10.7 data downloads
  * Fixed a bug in some versions where empty time indexes cannot be evaluated

[0.0.9] - 2022-12-21
--------------------
* Deprecations
  * Added warnings for the F10.7 and Kp tags that load data belonging in
  their own Instruments
* Enhancements
  * Added tests for Python 3.6.8, continuing support for older systems
  * Added a cron job for testing
  * Added an instrument for the LASP MgII core-to-wing index
  * Added functions for general LISIRD downloads

[0.0.8] - 2022-11-29
--------------------
* Bugs
  * Fixed F10.7 prelim and daily metadata to allow the fill value to keep the
    same type as the data
* Maintenance
  * Updated the GitHub Action version numbers
  * Updated syntax for pysat instrument testing suite
  * Remove deprecated pytest syntax (backwards support for nose)
  * Removed deprecated pandas syntax (iteritems)
  * Added Github action workflow using the latest pysat RC
  * Added new tags for the sw_kp instrument's GFZ data, 'def' and 'now', to
    replace ''

[0.0.7] - 2022-09-15
--------------------
* Updated `sw_f107` to allow reading old and new `historic` data file format
* Added exampled to the documentation for F10.7 and Kp methods
* Captured JSON error in historic F10.7 downloads and wrapped it with a logger
  message informing the user that their date may not be in the database
* Removed warning for not using the deprecated `freq` kwarg
* Removed deprecated function `load_csv_data`

[0.0.6] - 2022-07-08
--------------------
* Updated `sw_f107` to reflect changes in the `historic` data file format

[0.0.5] - 2022-06-10
--------------------
* Updated the docstrings to conform to pysat standards
* Added docstring tests to Flake8 portion of CI testing
* Fixed bug in `combine_kp` that occurs if no times are provided
* Improved unit test style and expanded unit test coverage
* Updated package organization documentation
* Added a function to normalize ACE SWEPAM variables as described in the OMNI
  processing guide
* Deprecated `load_csv_data` method, which was moved to pysat
* Added the LASP predicted Dst to the Dst Instrument
* Updated pandas usage to remove existing deprecation warnings
* Updated `pysat.Instrument.load` calls to remove `use_header` deprecation
  warning

[0.0.4] - 2021-05-19
--------------------
* New Logo
* Implements GitHub Actions for primary CI testing
* Updated tested python versions
* Removed non-document testing from Travis-CI and updated installation method
* Updated redirected links
* Improved PEP8 compliance
* Separated ACE instrument into four, following standard pysat practice of
  grouping satellite instruments using the satellite mission as the platform.
* Made standard Kp loading more robust
* Fixed bugs where current time used local time zone instead of UTC
* Added PyPi links to README and documentation
* Deprecated F10.7 instrument tag 'all' and '', replacing them with 'historic'
* Improved F10.7 instrument routines by combining similar code blocks
* Fixed F10.7 load/list bugs that lead to duplicate data entries
* Fixed Dst load bugs when loading multiple days of data
* Replaced Dst tag '' with 'noaa', making it easy to add other sources
* Moved all instrument support routines to appropriate `methods` sub-module

[0.0.3] - 2021-01-15
--------------------
* Fixes bugs in configuration and zenodo files
* Added pysat version restriction to requirements.txt

[0.0.2] - 2021-01-11
--------------------
* Added real-time ACE instrument
* Fixed bugs and restructured code to comply with changes in pysat-3.0
* Added user documentation
* Simplified setup and testing environments
* Separated space weather methods into sub-modules by instrument

[0.0.1] - 2020-08-13
--------------------
* Initial port of existing routines from pysat
