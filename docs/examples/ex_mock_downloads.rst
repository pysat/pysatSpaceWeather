.. _exmockdown:

Mock downloads
==============

:py:mod:`pysatSpaceWeather` differs from :py:mod:`pysat` by allowing
:py:class:`~pysat._instrument.Instrument` downloads to "download" data from
a local directory. This allows the user to have full control over the remote
access, while still allowing :py:mod:`pysat` to handle the data extraction and
file handling.

When using the mock-download option, :py:mod:`pysatSpaceWeather` requires that
you specify the local directory where you have stored the desired data files.
If you don't employ this option, downloads will be attempted from the remote
source. If you do employ this option and the directory is wrong, and IOError
will be raised. If instead the expected file is missing, a logging Information
message will be returned.

::

   import pysat
   import pysatSpaceWeather as py_sw

   f107 = pysat.Instrument(inst_module=py_sw.instruments.sw_f107, tag='45day')

   # 'Download' the data from a local directory 
   f107.download(start=f107.tomorrow(), mock_download_dir='my/data/directory')


These data files must have the same name as the remote file. In instances where
there is no remote filename (e.g., when "downloading" data from LISIRD), the
filename should reflect the internal name used by :py:mod:`pysatSpaceWeather`.
The locations and expected filenames for each of the Instruments are provided
in the table below. In this table, YYYY stands for the 4-digit year, MM stands
for the 2-digit month, and DD stands for the 2-digit day-of-month. QUERY is a
placeholder for a index and date dependent query needed to return the desired
data. See the GFZ and LISIRD methods to see how the queries are constructed.

+------------------------------------------------------------------------+------------------------------------+----------------------------------------------------------------------------------------------------------------------------+
| Remote Location                                                        | Filename                           | Instrument(s)                                                                                                              |
+========================================================================+====================================+============================================================================================================================+
| https://services.swpc.noaa.gov/text/                                   | 3-day-geomag-forecast.txt          | sw-ap-forecast, sw-kp-forecast, sw-stormprob-forecast                                                                      |
|                                                                        | 3-day-solar-geomag-predictions.txt | sw-ap-preciction, sw-f107-forecast, sw-flare-prediction, sw-kp-preciction, sw-polarcap-prediction, sw-stormprob-prediction |
|                                                                        | 45-day-ap-forecast.txt             | sw-f107-45day, sw-ap-45day                                                                                                 |
|                                                                        | ace-epam.txt                       | ace-epam-realtime                                                                                                          |
|                                                                        | ace-magnetometer.txt               | ace-mag-realtime                                                                                                           |
|                                                                        | ace-sis.txt                        | ace-sis-realtime                                                                                                           |
|                                                                        | ace-swepam.txt                     | ace-swepam-realtime                                                                                                        |
|                                                                        | daily-geomagnetic-indices.txt      | sw-ap-recent, sw-kp-recent                                                                                                 |
|                                                                        | daily-solar-indices.txt            | sw-ssn-daily, sw-f107-daily, sw-flare-daily, sw-sbfield-daily                                                              |
+------------------------------------------------------------------------+------------------------------------+----------------------------------------------------------------------------------------------------------------------------+
| https://sohoftp.nascom.nasa.gov/sdb/ace/daily/                         | YYYYMMDD_ace_epam_5m.txt           | ace-epam-historic                                                                                                          |
|                                                                        | YYYYMMDD_ace_mag_1m.txt            | ace-mag-historic                                                                                                           |
|                                                                        | YYYYMMDD_ace_sis_5m.txt            | ace-sis-historic                                                                                                           |
|                                                                        | YYYYMMDD_ace_swepam_1m.txt         | ace-swepam-historic                                                                                                        |
+------------------------------------------------------------------------+------------------------------------+----------------------------------------------------------------------------------------------------------------------------+
| ftp://ftp.swpc.noaa.gov/pub/indices/old_indices                        | YYYY_DSD.txt                       | sw-ssn-prelim, sw-f107-prelim, sw-flare-prelim, sw-sbfield-prelim                                                          |
+------------------------------------------------------------------------+------------------------------------+----------------------------------------------------------------------------------------------------------------------------+
| https://kp.gfz-potsdam.de/app/json/?QUERY                              | Fadj_YYYY-MM.txt                   | sw-f107-now-adj                                                                                                            |
|                                                                        | Fobs_YYYY-MM.txt                   | sw-f107-now-obs                                                                                                            |
|                                                                        | Hp30_YYYY-MM.txt                   | sw-hpo-now-30min                                                                                                           |
|                                                                        | Hp60_YYYY-MM.txt                   | sw-hpo-now-60min                                                                                                           |
|                                                                        | SN_YYYY-MM.txt                     | sw-ssn-now                                                                                                                 |
|                                                                        | ap30_YYYY-MM.txt                   | sw-apo-now-30min                                                                                                           |
|                                                                        | ap60_YYYY-MM.txt                   | sw-apo-now-60min                                                                                                           |
+------------------------------------------------------------------------+------------------------------------+----------------------------------------------------------------------------------------------------------------------------+
| https://datapub.gfz-potsdam.de/download/10.5880.Kp.0001/Kp_nowcast/    | Kp_nowYYYY.wdc                     | sw-ap-now, sw-cp-now, sw-kp-now                                                                                            |
+------------------------------------------------------------------------+------------------------------------+----------------------------------------------------------------------------------------------------------------------------+
| https://datapub.gfz-potsdam.de/download/10.5880.Kp.0001/Kp_definitive/ | kp_defYYYY.wdc                     | sw-ap-def, sw-cp-def, sw-kp-def                                                                                            |
+------------------------------------------------------------------------+------------------------------------+----------------------------------------------------------------------------------------------------------------------------+
| ftp://ftp.ngdc.noaa.gov/STP/GEOMAGNETIC_DATA/INDICES/DST               | dstYYYY.txt                        | sw-dst-noaa                                                                                                                |
+------------------------------------------------------------------------+------------------------------------+----------------------------------------------------------------------------------------------------------------------------+
| https://lasp.colorado.edu/lisird/latis/dap/QUERY                       | f107_monthly_YYYY-MM.txt           | sw-f107-historic                                                                                                           |
|                                                                        | mgii_composite_YYYY-MM.txt         | sw-mgii-composite                                                                                                          |
|                                                                        | mgii_sorce_YYYY-MM-DD.txt          | sw-mgii-sorce                                                                                                              |
+------------------------------------------------------------------------+------------------------------------+----------------------------------------------------------------------------------------------------------------------------+
| https://lasp.colorado.edu/space_weather/dsttemerin/                    | ae_last_96_hrs.txt                 | sw-ae-lasp                                                                                                                 |
|                                                                        | al_last_96_hrs.txt                 | sw-al-lasp                                                                                                                 |
|                                                                        | au_last_96_hrs.txt                 | sw-au-lasp                                                                                                                 |
|                                                                        | dst_last_96_hrs.txt                | sw-dst-lasp                                                                                                                |
+------------------------------------------------------------------------+------------------------------------+----------------------------------------------------------------------------------------------------------------------------+
