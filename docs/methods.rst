Methods
=======

Several methods exist to help combine multiple data sets and convert between
equivalent indices.

ACE
---

Supports the ACE instrument by providing reference and acknowledgement
information.


.. automodule:: pysatSpaceWeather.instruments.methods.ace
   :members:

Dst
---

Supports the Dst ring current index by providing reference and acknowledgement
information.


.. automodule:: pysatSpaceWeather.instruments.methods.dst
   :members:

F \ :sub:`10.7`\
----------------

Supports the F \ :sub:`10.7`\  radio flux by providing reference and
acknowledgement information as well as a routine to combine
F \ :sub:`10.7`\  data obtained from multiple sources.


.. automodule:: pysatSpaceWeather.instruments.methods.f107
   :members:


General
-------

General functions that are useful across platforms.


.. automodule:: pysatSpaceWeather.instruments.methods.general
   :members:


GFZ
---

Supports the German Research Centre for Geosciences at Potsdam (GFZ) data
products.


.. automodule:: pysatSpaceWeather.instruments.methods.gfz
   :members:


Kp and Ap
---------
Supports the Kp instrument by providing reference and acknowledgement
information, a routine to combine Kp from multiple sources, routines to convert
between Kp and Ap, and a routine that uses Kp data as a geomagnetic activity
filter for other data sets.


.. automodule:: pysatSpaceWeather.instruments.methods.kp_ap
   :members:


SWPC
----

Supports the Space Weather Prediction Center (SWPC) data products.


.. automodule:: pysatSpaceWeather.instruments.methods.swpc
   :members:
