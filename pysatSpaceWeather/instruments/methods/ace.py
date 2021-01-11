# -*- coding: utf-8 -*-.
"""Provides default routines for the real-time ACE instruments

"""


def acknowledgements(src):
    """Returns acknowledgements for the specified ACE instrument

    Parameters
    ----------
    src : string
        Name of the ACE instrument data source

    Returns
    -------
    ref : string
        Acknowledgements for the ACE instrument

    """

    ackn = {'sw': ''.join(['NOAA provided funds for the modification of the ',
                           'ACE transmitter to enable the broadcast of the ',
                           'real-time data and also funds to the instrument ',
                           'teams to provide the algorithms for processing ',
                           'the real-time data.'])}

    return ackn[src]


def references(iname):
    """Returns references for the specified ACE instrument

    Parameters
    ----------
    iname : string
        Name of the ACE instrument

    Returns
    -------
    ref : string
        Reference for the ACE instrument paper

    """

    refs = {'mag': "".join(["'The ACE Magnetic Field Experiment', ",
                            "C. W. Smith, M. H. Acuna, L. F. Burlaga, ",
                            "J. L'Heureux, N. F. Ness and J. Scheifele, ",
                            "Space Science Reviews, 86, 613-632 (1998)."]),
            'epam': ''.join(['Gold, R. E., S. M. Krimigis, S. E. Hawkins, ',
                             'D. K. Haggerty, D. A. Lohr, E. Fiore, ',
                             'T. P. Armstrong, G. Holland, L. J. Lanzerotti,',
                             ' Electron, Proton and Alpha Monitor on the ',
                             'Advanced Composition Explorer Spacecraft, ',
                             'Space Sci. Rev., 86, 541, 1998.']),
            'swepam': ''.join(['McComas, D., Bame, S., Barker, P. et al. ',
                               'Solar Wind Electron Proton Alpha Monitor ',
                               '(SWEPAM) for the Advanced Composition ',
                               'Explorer. Space Science Reviews 86, 563–612',
                               ' (1998). ',
                               'https://doi.org/10.1023/A:1005040232597']),
            'sis': ''.join(['Stone, E., Cohen, C., Cook, W. et al. The ',
                            'Solar Isotope Spectrometer for the Advanced ',
                            'Composition Explorer. Space Science Reviews ',
                            '86, 357–408 (1998). ',
                            'https://doi.org/10.1023/A:1005027929871'])}

    return refs[iname]
