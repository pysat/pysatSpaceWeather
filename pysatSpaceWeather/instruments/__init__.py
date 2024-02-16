from pysatSpaceWeather.instruments import methods  # noqa F401

__all__ = ['ace_epam', 'ace_mag', 'ace_sis', 'ace_swepam', 'sw_ae', 'sw_al',
           'sw_au', 'sw_ap', 'sw_apo', 'sw_cp', 'sw_dst', 'sw_f107', 'sw_flare',
           'sw_hpo', 'sw_kp', 'sw_mgii', 'sw_polarcap', 'sw_sbfield', 'sw_ssn',
           'sw_stormprob']

for inst in __all__:
    exec("from pysatSpaceWeather.instruments import {inst}".format(inst=inst))
