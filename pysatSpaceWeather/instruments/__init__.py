__all__ = ['sw_dst', 'sw_f107', 'sw_kp']

for inst in __all__:
    exec("from pysatSpaceWeather.instruments import {x}".format(x=inst))
