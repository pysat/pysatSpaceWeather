# -*- coding: utf-8 -*-.
"""Provides default routines for Dst

"""


def acknowledgements(name, tag):
    """Returns acknowledgements for space weather dataset

    Parameters
    ----------
    name : string
        Name of space weather index, eg, dst, f107, kp
    tag : string
        Tag of the space weather index

    """

    ackn = {'dst': {'': 'Dst is maintained at NCEI (formerly NGDC) at NOAA'}}

    return ackn[name][tag]


def references(name, tag):
    """Returns references for space weather dataset

    Parameters
    ----------
    name : string
        Name of space weather index, eg, dst, f107, kp
    tag : string
        Tag of the space weather index

    """

    refs = {'dst': {'': ''.join([
        'See referenece list and publication at: Sugiura M. and T. Kamei, '
        'http://wdc.kugi.kyoto-u.ac.jp/dstdir/dst2/onDstindex.html, ',
        'last updated June 1991, accessed Dec 2020'])}}

    return refs[name][tag]
