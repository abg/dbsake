"""
dbsake.util.fmt
~~~~~~~~~~~~~~

Formatting methods
"""
from __future__ import division
from __future__ import unicode_literals


def filesize(value):
    bytes = float(value)
    base = 1024
    prefixes = "KMGTPEZY"
    if bytes == 1:
        return '1B   '
    elif bytes < base:
        return '%dB  ' % bytes
    else:
        for i, prefix in enumerate(prefixes):
            unit = base ** (i + 2)
            if bytes < unit:
                return '%.1f%s' % ((base * bytes / unit), prefix)
        return '%.1f%s' % ((base * bytes / unit), prefix)


def timespan(seconds):
    """Convert a number of seconds to a human friendly string"""
    units = [
        ('w', 604800),
        ('d', 86400),
        ('h', 3600),
        ('m', 60),
    ]
    result = ''
    for name, n_seconds in units:
        unit_value, seconds = divmod(seconds, n_seconds)
        if unit_value != 0:
            result += "%d%s" % (unit_value, name)
    result += '%ds' % seconds
    return result
