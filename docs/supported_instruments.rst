Supported Instruments
=====================

ACE
---

Supports ACE Magnetometer data provided by the Space Weather Prediction Center
(SWPC) for use as real-time and historic measures of the solar wind.
Information about this data set can be found at the
`SWPC ACE Solar-Wind page <https://www.swpc.noaa.gov/products/ace-real-time-solar-wind>`_.


.. automodule:: pysatSpaceWeather.instruments.sw_ace
   :members:

Dst
---

The Disturbance Storm Time (Dst) Index is a measure of magnetic activity
associated with the ring current.  The National Geophysical Data Center (NGDC)
maintains the
`current database <https://www.ngdc.noaa.gov/stp/geomag/dst.html>`_ from which
the Dst is downloaded.  You can learn more about the Dst Index at the
`WDC Kyoto Observatory page <http://wdc.kugi.kyoto-u.ac.jp/dstdir/index.html>`_.


.. automodule:: pysatSpaceWeather.instruments.sw_dst
   :members:

F \ :sub:`10.7`\
----------------

F \ :sub:`10.7`\  is the 10.7 cm radio solar flux (measured in solar flux units,
sfu) `[Cortie 1912] <http://adsabs.harvard.edu/full/1912MNRAS..73...52C>`_.
Historic indices, real-time indices, and forecasted indices are available from
`LASP <https://lasp.colorado.edu/lisird/data/noaa_radio_flux/>`_ and the
`SWPC F107 page <https://www.swpc.noaa.gov/phenomena/f107-cm-radio-emissions>`_.


.. automodule:: pysatSpaceWeather.instruments.sw_f107
   :members:

Kp
---

Kp is a geomagnetic index that reflects the magnitude of geomagnetic
disturbances at Earth.  Historic, recent (last 30 days), and forecasted values
are available from the German Research Centre for Geosciences at Potsdam,
`GFZ <https://www.gfz-potsdam.de/en/kp-index/>`_, and the
`SWPC Kp page <https://www.swpc.noaa.gov/products/planetary-k-index>`_.


.. automodule:: pysatSpaceWeather.instruments.sw_kp
   :members:
