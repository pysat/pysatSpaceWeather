Methods
=======

Several methods exist to help combine multiple data sets and convert between
equivalent indices.

ACE
---

Supports the SAMI2 (Sami2 is Another Model of the Ionosphere) model through the
sami2py interface. Sami2py is a python module that runs the SAMI2 model, as well
as archives, loads and plots the resulting modeled values. SAMI2 is a model
developed by the Naval Research Laboratory to simulate the motions of plasma
in a 2D ionospheric environment along a dipole magnetic field [Huba et al, 2000].
Information about this model can be found at the
`sami2py github page <https://github.com/sami2py/sami2py>`_,
along with a list of
`references <https://sami2py.readthedocs.io/en/latest/introduction.html#references>`_.

.. automodule:: pysatSpaceWeather.methods.ace
   :members:

SW
---

Supports the UCAR (University Corporation for Atmospheric Research) model,
Thermosphere-Ionosphere-Electrodynamics General Circulation Model (TIE-GCM).
Information about this model can be found at the
`UCAR TIE-GCM website <https://www.hao.ucar.edu/modeling/tgcm/tie.php>`_,
along with a list of the
`principle papers <https://www.hao.ucar.edu/modeling/tgcm/TgcmPrincipalPapers.pdf>`_.

.. automodule:: pysatSpaceWeather.methods.sw
   :members:
