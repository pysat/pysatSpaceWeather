.. _exmultdown:

Downloading data from multiple Instruments
==========================================

Unlike most data sets, space weather index data sets often contain a combination
of related indices. This means that data from multiple
:py:class:`pysat.Instrument` sub-modules may be available in a single file.
Starting in :py:mod:`pysatSpaceWeather` version 0.1.0, this data is saved for
all :py:class:`pysat.Instrument` sub-modules when downloading any one of them.
In this way, downloads are minimized and no data sets are hidden or thrown away.
The following example returns both F\ :sub:`10.7`\ and Ap forecasts from SWPC.
Previously, this data was contained in
:py:mod:`pysatSpaceWeather.instruments.sw_f107`, which does not contain Ap data
for all ``tag`` values.

::

   import pysat
   import pysatSpaceWeather as py_sw

   f107 = pysat.Instrument(inst_module=py_sw.instruments.sw_f107, tag='45day')
   ap = pysat.Instrument(inst_module=py_sw.instruments.sw_ap, tag='45day')

   # Test to see this data hasn't already been downloaded
   assert (ap.today() not in f107.files.files) and (ap.today()
                                                    not in ap.files.files)

   # Download both data sets using only one Instrument
   f107.download(start=f107.tomorrow())

   # Show that both files have been downloaded
   print(f107.files.files[f107.today()], ap.files.files[ap.today()])


This will yield ``f107_45day_YYYY-MM-DD.txt ap_45day_YYYY-MM-DD.txt``, where
YYYY-MM-DD is the day you run this example.  The table below shows a list of
the :py:class:`pysat.Instrument` sub-modules and tags that download multiple
data sets.  When possible, the same tag has been used across
:py:class:`pysat.Instrument` sub-modules.


+----------------------+----------+------------+------------+------------+
| Remote Data Set      | Platform | Name       | Tag(s)     | Inst ID(s) |
+======================+==========+============+============+============+
| GFZ Kp               | SW       | Kp         | def, now   |            |
+----------------------+----------+------------+------------+------------+
|                      |          | Ap         |            |            |
+----------------------+----------+------------+------------+------------+
|                      |          | Cp         |            |            |
+----------------------+----------+------------+------------+------------+
| SWPC Daily DSD       | SW       | F107       | daily      |            |
+----------------------+----------+------------+------------+------------+
|                      |          | Flare      |            |            |
+----------------------+----------+------------+------------+------------+
|                      |          | SSN        |            |            |
+----------------------+----------+------------+------------+------------+
|                      |          | SBField    |            |            |
+----------------------+----------+------------+------------+------------+
| SWPC Prelim DSD      | SW       | F107       | prelim     |            |
+----------------------+----------+------------+------------+------------+
|                      |          | Flare      |            |            |
+----------------------+----------+------------+------------+------------+
|                      |          | SSN        |            |            |
+----------------------+----------+------------+------------+------------+
|                      |          | SBField    |            |            |
+----------------------+----------+------------+------------+------------+
| SWPC 3-day Solar-Geo | SW       | F107       | forecast   |            |
+----------------------+----------+------------+------------+------------+
| Predictions          |          | Kp         | prediction |            |
+----------------------+----------+------------+------------+------------+
|                      |          | Ap         |            |            |
+----------------------+----------+------------+------------+------------+
|                      |          | Storm-Prob |            |            |
+----------------------+----------+------------+------------+------------+
|                      |          | Flare      |            |            |
+----------------------+----------+------------+------------+------------+
|                      |          | Polar-Cap  |            |            |
+----------------------+----------+------------+------------+------------+
| SWPC 3-day Geomag    | SW       | Kp         | forecast   |            |
+----------------------+----------+------------+------------+------------+
| Forecast             |          | Ap         |            |            |
+----------------------+----------+------------+------------+------------+
|                      |          | Storm-Prob |            |            |
+----------------------+----------+------------+------------+------------+
| SWPC Daily Geomag    | SW       | Kp         | recent     |            |
+----------------------+----------+------------+------------+------------+
|                      |          | Ap         |            |            |
+----------------------+----------+------------+------------+------------+
| SWPC 45-day Forecast | SW       | F107       | 45day      |            |
+----------------------+----------+------------+------------+------------+
|                      |          | Ap         |            |            |
+----------------------+----------+------------+------------+------------+
