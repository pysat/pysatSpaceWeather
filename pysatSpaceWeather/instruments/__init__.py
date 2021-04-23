from pysatSpaceWeather.instruments import methods  # noqa F401

__all__ = ['ace_epam', 'ace_mag', 'ace_sis', 'ace_swepam',
           'sw_dst', 'sw_f107', 'sw_kp']

for inst in __all__:
    exec("from pysatSpaceWeather.instruments import {x}".format(x=inst))
