# -*- coding: utf-8 -*-.
"""Provides default routines for Dst."""


def acknowledgements(tag):
    """Define the acknowledgements for the Dst data.

    Parameters
    ----------
    tag : str
        Tag of the space weather index

    Returns
    -------
    ackn : str
        Acknowledgements string associated with the appropriate Dst tag.

    """

    ackn = {'noaa': 'Dst is maintained at NCEI (formerly NGDC) at NOAA',
            'lasp': ''.join(['Preliminary Dst predictions are provided by ',
                             'LASP, contact Xinlin Li for more details ',
                             '<xinlin.li@lasp.colorado.edu>'])}

    return ackn[tag]


def references(tag):
    """Define the references for the Dst data.

    Parameters
    ----------
    tag : string
        Tag of the space weather index

    Returns
    -------
    refs : str
        Reference string associated with the appropriate Dst tag.

    """

    refs = {'noaa': ''.join(['See referenece list and publication at: ',
                             'Sugiura M. and T. Kamei, http://',
                             'wdc.kugi.kyoto-u.ac.jp/dstdir/dst2/',
                             'onDstindex.html, last updated June 1991, ',
                             'accessed Dec 2020']),
            'lasp': ''.join(['A New Model for the Prediction of Dst on the ',
                             'Basis of the Solar Wind [Temerin and Li, 2002] ',
                             'and Dst model for 1995-2002 [Temerin and Li, ',
                             '2006]'])}

    return refs[tag]
