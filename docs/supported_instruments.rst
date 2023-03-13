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


.. _sw-inst:
SW
---

The Space Weather (SW) platform encompasses space weather indices that may be
found across a variety of platforms.  Many of the remote centers that provide
these data sets include multiple types of data in each file.  From
:py:mod:`pysatSpaceWeather` version 0.1.0, the remote information is separated
by :py:class:`pysat.Instrument` and saved into appropriate files.  For example,
the definitive Kp data from the German Research Centre for Geosciences at
Potsdam (GFZ) will also download Ap and Cp data files.


.. _sw-ap-inst:

Ap
^^^

Ap is a geomagnetic index that reflects the magnitude of geomagnetic
disturbances at Earth, but unlike the Kp uses a linear scale.  Historic, recent
(last 30 days), and forecasted values are available from 
`GFZ <https://www.gfz-potsdam.de/en/kp-index/>`_ and the
`SWPC Forecasts page <https://www.swpc.noaa.gov/forecasts>`_.


.. automodule:: pysatSpaceWeather.instruments.sw_ap
   :members:


.. _sw-apo-inst:

apo
^^^

apo is a linear (half)-hourly, planetary, open-ended, geomagnetic index that
reflects the magnitude of geomagnetic disturbances at Earth. It is like Ap, but
does not have an upper limit. Values from 1995 onwards are available from 
`GFZ <https://kp.gfz-potsdam.de/en/hp30-hp60>`_.


.. automodule:: pysatSpaceWeather.instruments.sw_apo
   :members:


.. _sw-cp-inst:

Cp
^^^

Cp is a derivative geomagnetic index that provides a qualitative estimate of the
overall level of magnetic activity for the day.  The C9 index provides the same
information on a scale from 0-9 instead of 0.0-2.5. Historic values are
available from
`GFZ <https://spaceweather.gfz-potsdam.de/products-data/nowcasts/nowcast-kp-index/geomagnetic-indices-ap-ap-cp-and-c9-derivative-indices>`_.


.. automodule:: pysatSpaceWeather.instruments.sw_cp
   :members:


.. _sw-dst-inst:

Dst
^^^

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


.. _sw-f107-inst:

F \ :sub:`10.7`\
^^^^^^^^^^^^^^^^

F \ :sub:`10.7`\  is the 10.7 cm radio solar flux (measured in solar flux units,
sfu) `[Cortie 1912] <http://adsabs.harvard.edu/full/1912MNRAS..73...52C>`_.
Historic indices, real-time indices, and forecasted indices are available from
`LASP <https://lasp.colorado.edu/lisird/data/noaa_radio_flux/>`_ and the
`SWPC F107 page <https://www.swpc.noaa.gov/phenomena/f107-cm-radio-emissions>`_.


.. automodule:: pysatSpaceWeather.instruments.sw_f107
   :members:


.. _sw-flare-inst:

Solar Flares
^^^^^^^^^^^^

Solar flares have been monitored for decades, and the data has been compiled
into standard measurements from different data sets. Historic indices,
real-time indices, and forecasted indices are available from
`SWPC <https://www.swpc.noaa.gov/phenomena>`_.


.. automodule:: pysatSpaceWeather.instruments.sw_flare
   :members:


.. _sw-hpo-inst:

Hpo
^^^

Hpo is a (half)-Hourly, Planetary, Open-ended, geomagnetic index that
reflects the magnitude of geomagnetic disturbances at Earth. It is like Kp, but
does not have an upper limit. Values from 1995 onwards are available from 
`GFZ <https://kp.gfz-potsdam.de/en/hp30-hp60>`_.


.. automodule:: pysatSpaceWeather.instruments.sw_hpo
   :members:



.. _sw-kp-inst:

Kp
^^^

Kp is a geomagnetic index that reflects the magnitude of geomagnetic
disturbances at Earth.  Historic, recent (last 30 days), and forecasted values
are available from `GFZ <https://www.gfz-potsdam.de/en/kp-index/>`_, and the
`SWPC Kp page <https://www.swpc.noaa.gov/products/planetary-k-index>`_.


.. automodule:: pysatSpaceWeather.instruments.sw_kp
   :members:


.. _mgii-inst:

MgII Core-to-Wing Ratio
^^^^^^^^^^^^^^^^^^^^^^^

The core-to-wing ratio of the solar MgII line is a proxy for solar chromospheric
variability.  It has been used to extract a precise measurement of solar
activity at Earth.  The two data sets provided by LASP together provide index
values from 1978 through 2020.


.. automodule:: pysatSpaceWeather.instruments.sw_mgii
   :members:

.. _sw-pc-inst:

Polar Cap
^^^^^^^^^

Polar cap indices have been developed to provide information about high-latitude
conditions and inform ionospheric space weather models. Currently, this
Instrument provides absorption predictions from SWPC.

.. automodule:: pysatSpaceWeather.instruments.sw_polarcap
   :members:


.. _sw-sbfield-inst:

Solar Magnetic Field
^^^^^^^^^^^^^^^^^^^^

The solar mean field provides a measure of of mean solar magnetic field using
full-disk optical observations of the iron line.  The first observations were
made at Stanford by
`Scherrer et al. <https://link.springer.com/article/10.1007/BF00159925>`_.

.. automodule:: pysatSpaceWeather.instruments.sw_sbfield
   :members:


.. _sw-ssn-inst:

Sunspot Number
^^^^^^^^^^^^^^

The Sunspot Number (SSN) is one of the oldest continuously measured solar
indices. Currently, this Instrument provides preliminary and daily values from
SWPC (for example, here is the
`forecast page <https://www.swpc.noaa.gov/products/predicted-sunspot-number-and-radio-flux>`_).

.. automodule:: pysatSpaceWeather.instruments.sw_ssn
   :members:


.. _sw-stormprob-inst:

Storm Probability
^^^^^^^^^^^^^^^^^

Geomagnetic storm predictions are provided by SWPC for global, high-latitude,
and mid-latitude regions. SWPC uses the
`NOAA SW scales <https://www.swpc.noaa.gov/noaa-scales-explanation>`_, which
are explained here.

.. automodule:: pysatSpaceWeather.instruments.sw_stormprob
   :members:
