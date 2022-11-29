.. _exinit:

Loading F\ :sub:`10.7`\
========================

pysatSpaceWeather uses `pysat <https://github.com/pysat/pysat>`_ to load
different historical, real-time, and forecasted solar, geomagnetic, and other
space weather indices.  As specified in the
`pysat tutorial <https://pysat.readthedocs.io/en/latest/tutorial.html>`_,
data may be loaded using the following commands.  Historic F\ :sub:`10.7`\  is
used as an example.

::


   import pysat
   import pysatSpaceWeather as py_sw

   f107 = pysat.Instrument(inst_module=py_sw.instruments.sw_f107,
                           tag='historic', update_files=True)
   f107.download(start=f107.lasp_stime, stop=f107.today())
   f107.load()
   print(f107.data)


The output includes all available historic data (as implied by the tag name),
including the specified date.  This data set starts on 14 February 1947, as
indicated by the special instrument attribute `f107.lasp_stime`, and will
not reach up to the present day.  At the time of publication this produces the
output shown below (the index header has been added here for clarity).

::


   <Index>     f107  f107_adjusted  f107_observed
   1947-02-14  253.9          253.9            NaN
   1947-02-17  228.5          228.5            NaN
   1947-02-19  178.8          178.8            NaN
   1947-02-20  163.7          163.7            NaN
   1947-02-24  164.1          164.1            NaN
   ...           ...            ...            ...
   2018-04-27   69.6           69.6           68.7
   2018-04-28   71.1           71.1           70.2
   2018-04-29   72.2           72.2           71.1
   2018-04-30   71.3           71.3           70.2
   
   [25367 rows x 3 columns]


