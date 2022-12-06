.. _supported_inst:

Supported Instruments
=====================


.. _ace-inst:

ACE
---

The Space Weather Prediction Center (SWPC) provides several Advanced
Composition Explorer (ACE) instrument data sets for use as real-time and
historic measurements of the solar wind.  This differs from the ACE scientific
data, which is available at a greater latency from
`CDAWeb <https://cdaweb.gsfc.nasa.gov/index.html/>`_. Information about these
data sets can be found at the `SWPC ACE Solar-Wind page
<https://www.swpc.noaa.gov/products/ace-real-time-solar-wind>`_.


.. _ace-epam-inst:

ACE EPAM
^^^^^^^^

EPAM is the Electron, Proton, and Alpha Monitor onboard ACE.


.. automodule:: pysatSpaceWeather.instruments.ace_epam
   :members:


.. _ace-mag-inst:

ACE MAG
^^^^^^^

Supports ACE Magnetometer data.


.. automodule:: pysatSpaceWeather.instruments.ace_mag
   :members:


.. _ace-sis-inst:

ACE SIS
^^^^^^^

Supports ACE Solar Isotope Spectrometer data.


.. automodule:: pysatSpaceWeather.instruments.ace_sis
   :members:


.. _ace-swepam-inst:

ACE SWEPAM
^^^^^^^^^^

Supports ACE Solar Wind Electron Proton Alpha Monitor data.


.. automodule:: pysatSpaceWeather.instruments.ace_swepam
   :members:


.. _dst-inst:

Dst
---

The Disturbance Storm Time (Dst) Index is a measure of magnetic activity
associated with the ring current.  The National Geophysical Data Center (NGDC)
maintains the
`current database <https://www.ngdc.noaa.gov/stp/geomag/dst.html>`_ from which
the historic Dst is downloaded.
`LASP <https://lasp.colorado.edu/space_weather/dsttemerin/dsttemerin.html>`_
performs the calculates and provides the predicted Dst for the last 96 hours.
You can learn more about the Dst Index at the
`WDC Kyoto Observatory page <http://wdc.kugi.kyoto-u.ac.jp/dstdir/index.html>`_.


.. automodule:: pysatSpaceWeather.instruments.sw_dst
   :members:


.. _f107-inst:

F \ :sub:`10.7`\
----------------

F \ :sub:`10.7`\  is the 10.7 cm radio solar flux (measured in solar flux units,
sfu) `[Cortie 1912] <http://adsabs.harvard.edu/full/1912MNRAS..73...52C>`_.
Historic indices, real-time indices, and forecasted indices are available from
`LASP <https://lasp.colorado.edu/lisird/data/noaa_radio_flux/>`_ and the
`SWPC F107 page <https://www.swpc.noaa.gov/phenomena/f107-cm-radio-emissions>`_.


.. automodule:: pysatSpaceWeather.instruments.sw_f107
   :members:


.. _kp-inst:

Kp
---

Kp is a geomagnetic index that reflects the magnitude of geomagnetic
disturbances at Earth.  Historic, recent (last 30 days), and forecasted values
are available from the German Research Centre for Geosciences at Potsdam,
`GFZ <https://www.gfz-potsdam.de/en/kp-index/>`_, and the
`SWPC Kp page <https://www.swpc.noaa.gov/products/planetary-k-index>`_.


.. automodule:: pysatSpaceWeather.instruments.sw_kp
   :members:


.. _mgii-inst:

MgII Core-to-Wing Ratio
-----------------------

The core-to-wing ratio of the solar MgII line is a proxy for solar chromospheric
variability.  It has been used to extract a precise measurement of solar
activity at Earth.  The two data sets provided by LASP together provide index
values from 1978 through 2020.


.. automodule:: pysatSpaceWeather.instruments.sw_mgii
   :members:
