#!/usr/bin/env python
# -*- coding: utf-8 -*-.
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.3986138
#
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
"""Provides support routines for auroral electrojet indices."""


def acknowledgements(name, tag):
    """Define the acknowledgements for the index and data source.

    Parameters
    ----------
    name : str
        Name of the auroral electrojet index
    tag : str
        Tag of the auroral electrojet index

    Returns
    -------
    ackn : str
        Acknowledgements string associated with the appropriate auroral
        electrojet tag.

    """

    ackn = {'lasp': ''.join(['Preliminary ', name.upper(), ' predictions are ',
                             'provided by LASP, contact Xinlin Li for more ',
                             'details <xinlin.li@lasp.colorado.edu>'])}

    return ackn[tag]


def references(name, tag):
    """Define the references for the auroral electrojet data.

    Parameters
    ----------
    name : str
        Name of the auroral electrojet index
    tag : string
        Tag of the space weather index

    Returns
    -------
    refs : str
        Reference string associated with the appropriate Dst tag.

    """

    davis = ''.join(['Davis, T. N., and Sugiura, M. (1966), Auroral electrojet',
                     ' activity index AE and its universal time variations, ',
                     'J. Geophys. Res., 71( 3), 785– 801, ',
                     'doi:10.1029/JZ071i003p00785.'])

    luo_au_al_ae = ''.join(['Luo, B., Li, X., Temerin, M., and Liu, S. (2013),',
                            'Prediction of the AU, AL, and AE indices using ',
                            'solar wind parameters, J. Geophys. Res. Space ',
                            'Physics, 118, 7683– 7694, ',
                            'doi:10.1002/2013JA019188.'])
    li_al = ''.join(['Li, X., Oh, K. S., and Temerin, M. (2007), Prediction ',
                     'of the AL index using solar wind parameters, J. ',
                     'Geophys. Res., 112, A06224, doi:10.1029/2006JA011918.'])

    refs = {'lasp': {'ae': '\n'.join([davis, luo_au_al_ae]),
                     'au': '\n'.join([davis, luo_au_al_ae]),
                     'al': '\n'.join([davis, li_al, luo_au_al_ae])}}

    return refs[tag][name]
