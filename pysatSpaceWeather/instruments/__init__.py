from pysatSpaceWeather.instruments import methods  # noqa F401

__all__ = ['sw_dst', 'sw_f107', 'sw_kp', 'sw_ace']

for inst in __all__:
    exec("from pysatSpaceWeather.instruments import {x}".format(x=inst))
