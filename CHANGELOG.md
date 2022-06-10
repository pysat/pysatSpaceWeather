Change Log
==========
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](https://semver.org/).

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
