<div align="left">
        <img height="0" width="0px">
        <img width="20%" src="https://raw.githubusercontent.com/pysat/pysatSpaceWeather/main/docs/figures/pysatSpaceWeather.png" alt="pysatSpaceWeather" title="pysatSpaceWeather"</img>
</div>

# pysatSpaceWeather: pysat support for Space Weather Indices
[![Build Status](https://travis-ci.com/pysat/pysatSpaceWeather.svg?branch=main)](https://travis-ci.com/pysat/pysatSpaceWeather)
[![Coverage Status](https://coveralls.io/repos/github/pysat/pysatSpaceWeather/badge.svg?branch=main)](https://coveralls.io/github/pysat/pysatSpaceWeather?branch=main)
[![DOI](https://zenodo.org/badge/287377838.svg)](https://zenodo.org/badge/latestdoi/287377838) [![Documentation](https://readthedocs.org/projects/pysatspaceweather/badge/?version=latest)](https://pysatspaceweather.readthedocs.io/en/latest/?badge=latest)


This module handles solar and geomagnetic indices needed for scientific and
operational projects.

# Installation

The following instructions provide a guide for installing pysatSpaceWeather and give
some examples on how to use the routines

### Prerequisites

pysatSpaceWeather uses common Python modules, as well as modules developed by
and for the Space Physics community.  This module officially supports
Python 3.6+.

| Common modules | Community modules |
| -------------- | ----------------- |
| netCDFF4       | pysat             |
| numpy          |                   |
| pandas         |                   |
| requests       |                   |
| xarray         |                   |

## GitHub Installatioon

Currently, the main way to get pysatSpaceWeather is through github.

```
git clone https://github.com/pysat/pysatSpaceWeather.git
```

Change directories into the repository folder and run the setup.py file.  For
a local install use the "--user" flag after "install".

```
cd pysatSpaceWeather/
python setup.py install
```

Note: pre-1.0.0 version
-----------------------
pysatSpaceWeather is currently in an initial development phase.  Much of the
API is being built off of the upcoming pysat 3.0.0 software in order to
streamline the usage and test coverage.  This version of pysat is planned for
release in Feb 2021.  Currently, you can access the develop version of this
through github:
```
git clone https://github.com/pysat/pysat.git
cd pysat
git checkout develop-3
python setup.py install
```
It should be noted that this is a working branch and is subject to change.

# Examples

The instrument modules are portable and designed to be run like any pysat
instrument.

```
import pysat
import pysatSpaceWeather
from pysatSpaceWeather.instruments import sw_dst

dst = pysat.Instrument(inst_module=sw_dst)
```

Another way to use the instruments in an external repository is to register the
instruments.  This only needs to be done the first time you load an instrument.
Afterward, pysat will identify them using the `platform` and `name` keywords.

```

pysat.utils.registry.register('pysatSpaceWeather.instruments.sw_dst')
dst = pysat.Instrument('sw', 'dst')
```
