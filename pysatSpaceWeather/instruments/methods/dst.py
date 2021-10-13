# -*- coding: utf-8 -*-.
"""Provides default routines for Dst."""


def acknowledgements(tag):
    """Defines the acknowledgements for the Dst data.

    Parameters
    ----------
    tag : str
        Tag of the space weather index

    Returns
    -------
    ackn : str
        Acknowledgements string associated with the appropriate Dst tag.

    """

    ackn = {'noaa': 'Dst is maintained at NCEI (formerly NGDC) at NOAA'}

    return ackn[tag]


def references(tag):
    """Defines the references for the Dst data.

    Parameters
    ----------
    tag : string
        Tag of the space weather index

    Returns
    -------
    refs : str
        Reference string associated with the appropriate Dst tag.

    """

    refs = {'noaa': ''.join([
        'See referenece list and publication at: Sugiura M. and T. Kamei, '
        'http://wdc.kugi.kyoto-u.ac.jp/dstdir/dst2/onDstindex.html, ',
        'last updated June 1991, accessed Dec 2020'])}

    return refs[tag]
