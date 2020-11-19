Installation
============

The following instructions will allow you to install pysatSpaceWeather.

Prerequisites
-------------

.. image:: figures/poweredbypysat.png
    :width: 150px
    :align: right
    :alt: powered by pysat Logo, blue planet with orbiting python


pysatSpaceWeather uses common Python modules, as well as modules developed by
and for the Space Physics community.  This module officially supports
Python 3.6+.

 ============== =================
 Common modules Community modules
 ============== =================
  netCDF4        pysat             
  numpy
  pandas
  requests
  xarray
 ============== =================


Installation Options
--------------------

1. Clone the git repository
::

   
   git clone https://github.com/pysat/pysatSpaceWeather.git


2. Install pysatSpaceWeather:
   Change directories into the repository folder and run the setup.py file.
   There are a few ways you can do this:

   A. Install on the system (root privileges required)::

	
        sudo python3 setup.py install
   B. Install at the user level::

	
        python3 setup.py install --user  
   C. Install with the intent to develop locally::

	
        python3 setup.py develop --user
