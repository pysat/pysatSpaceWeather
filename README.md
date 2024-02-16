<div align="left">
        <img height="0" width="0px">
        <img width="20%" src="https://raw.githubusercontent.com/pysat/pysatSpaceWeather/main/docs/figures/pysatSpaceWeather.png" alt="pysatSpaceWeather" title="pysatSpaceWeather" </img>
</div>

# pysatSpaceWeather: pysat support for Space Weather Indices
[![Pytest with Flake8](https://github.com/pysat/pysatSpaceWeather/actions/workflows/main.yml/badge.svg)](https://github.com/pysat/pysatSpaceWeather/actions/workflows/main.yml)
[![Coverage Status](https://coveralls.io/repos/github/pysat/pysatSpaceWeather/badge.svg?branch=main)](https://coveralls.io/github/pysat/pysatSpaceWeather?branch=main)
[![DOI](https://zenodo.org/badge/287377838.svg)](https://zenodo.org/badge/latestdoi/287377838) [![Documentation](https://readthedocs.org/projects/pysatspaceweather/badge/?version=latest)](https://pysatspaceweather.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/pysatSpaceWeather.svg)](https://badge.fury.io/py/pysatSpaceWeather)


This module handles solar and geomagnetic indices needed for scientific and
operational projects.

# Installation

The following instructions provide a guide for installing pysatSpaceWeather and
give some examples on how to use the routines.

## Prerequisites

pysatSpaceWeather uses common Python modules, as well as modules developed by
and for the Space Physics community.  This module officially supports
Python 3.7+.

| Common modules | Community modules |
| -------------- | ----------------- |
| netCDF4        | pysat >= 3.1.0    |
| numpy          |                   |
| pandas         |                   |
| requests       |                   |
| xarray         |                   |


## PyPi Installation
```
pip install pysatSpaceWeather
```

## GitHub Installation
```
git clone https://github.com/pysat/pysatSpaceWeather.git
```

Change directories into the repository folder and run the setup.py file.  For
a local install use the "--user" flag after "install".

```
cd pysatSpaceWeather/
python -m build .
pip install .
```

# Examples

The instrument modules are portable and designed to be run like any pysat
instrument.

```
import pysat
import pysatSpaceWeather
dst = pysat.Instrument(inst_module=pysatSpaceWeather.instruments.sw_dst)
```

Another way to use the instruments in an external repository is to register the
instruments.  This only needs to be done the first time you load an instrument.
Afterward, pysat will identify them using the `platform` and `name` keywords.

```
pysat.utils.registry.register('pysatSpaceWeather.instruments.sw_dst')
dst = pysat.Instrument('sw', 'dst')
```
