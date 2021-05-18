Change Log
==========
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](https://semver.org/).

[0.0.4] - 2021-05-19
--------------------
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
