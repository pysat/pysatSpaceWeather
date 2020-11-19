Loading F\ :sub:`10.7``\
========================

pysatSpaceWeather uses `pysat <https://github.com/pysat/pysat>`_ to load
different historical, real-time, and forecasted solar, geomagnetic, and other
space weather indices.  As specified in the
`pysat tutorial <https://pysat.readthedocs.io/en/latest/tutorial.html>`_,
data may be loaded using the following commands.  Historic F\ :sub:`10.7``\ is
used as an example.

::


   import datetime as dt
   import pysat
   import pysatSpaceWeather as py_sw

   old_time = dt.datetime(2012, 5, 14)
   f107 = pysat.Instrument(inst_module=py_sw.instruments.sw_f107, tag='all',
                           update_files=True)
   f107.download(start=old_time)
   f107.load(start=old_time)
   print(f107)


The output includes all available historic data (as implied by the tag name),
including the specified date.  This data set starts on 14 February 1947 and
will not reach up to the present day.
