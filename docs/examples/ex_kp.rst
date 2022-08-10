Load Kp from Multiple Sources
=============================

Following from the F\ :sub:`10.7`\ `example <>`_, :py:mod:`pysatSpaceWeather`
has a routine to combine several sources of Kp over different time periods.
This may be done using the
:py:func:`~pysatSpaceWeather.instruments.methods.kp_ap.combine_kp` function.

::


   import datetime as dt
   import pysat
   import pysatSpaceWeather as py_sw

   kp_his = pysat.Instrument(inst_module=py_sw.instruments.sw_kp,
                             tag='', update_files=True)
   kp_rec = pysat.Instrument(inst_module=py_sw.instruments.sw_kp,
                             tag='recent', update_files=True)
   kp_for = pysat.Instrument(inst_module=py_sw.instruments.sw_kp,
                             tag='forecast', update_files=True)

   # Set the time range
   stime = dt.datetime(1994, 1, 1)
   etime = kp_for.today()

   # If needed, download the data
   kp_his.download(start=stime, stop=etime)
   kp_rec.download(start=stime, stop=etime)
   kp_for.download(start=etime)

   # Combine the Kp sources for all available times
   kp = py_sw.instruments.methods.kp.combine_kp(kp_his, kp_rec, kp_for, stime,
                                                etime)

   # Check the combined Instrument index
   print(kp.index[[0, -1]])


This combined :py:class:`pysat.Instrument` can be used to plot the Kp over time.

::


   import matplotlib as mpl
   import matplotlib.pyplot as plt
   
   fig = plt.figure()
   ax = fig.add_subplot(111)

   ax.bar(kp.index, kp['kp'], color='b')
   ax.xaxis.set_major_formatter(mpl.dates.DateFormatter('%Y'))
   ax.xaxis.set_major_locator(mpl.dates.YearLocator(interval=3))
   ax.set_xlabel('Universal Time (Year C.E.)')
   ax.set_ylabel(r'Kp')

   # If not running in interactive mode
   plt.show()


INCLUDE FIGURE HERE


Convert Kp to ap
================

The Kp and ap have a well established relationship, which takes the logarithmic
Kp index and converts it to a linear scale that is easier to handle numerically.
The :py:func:`~pysatSpaceWeather.instruments.methods.kp_ap.convert_3hr_kp_to_ap`
converts Kp to ap, as shown below.

::
   py_sw.instruments.methods.kp_ap.convert_3hr_kp_to_ap(kp)

   print("Max: {:.1f} -> {.1f}, Min: {:.1f} -> {:.1f}".format(
       kp['Kp'].max(), kp['3hr_ap'].max(), kp['Kp'].min(), kp['3hr_ap'].min()))

This yields ``Max: 9.0 -> 400.0, Min: 0.0 -> 0.0``. 
