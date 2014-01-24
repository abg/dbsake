"""
dbsake.util
~~~~~~~~~~~

Utility methods used by dbsake
"""

import contextlib
import subprocess

from . import template

@contextlib.contextmanager
def stream_command(cmd, stdout):
    process = subprocess.Popen(cmd,
                               stdin=subprocess.PIPE,
                               stdout=stdout,
                               shell=True,
                               close_fds=True)
    yield process
    process.stdin.close()
    process.wait()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(cmd, returncode)

class Bunch(dict):
    """Access dict elements as object attributes

    >>> b = Bunch(foo='bar', bar='baz')
    >>> b.foo
    'bar'
    >>> b.argh = 'castle'
    >>> b['argh']
    'castle'
    >>> b.argh
    'castle
    """
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            # AttributeError: type object 'bunch' has no attribute 'baz'
            raise AttributeError('type {0!r} has no attribute {1!r}'.format(
                                    self.__class__.__name__, name))

    def __setattr__(self, name, value):
        self[name] = value

def format_filesize(value, binary=True):
    bytes = float(value)
    base = binary and 1024 or 1000
    prefixes = [
        (binary and 'KiB' or 'kB'),
        (binary and 'MiB' or 'MB'),
        (binary and 'GiB' or 'GB'),
        (binary and 'TiB' or 'TB'),
        (binary and 'PiB' or 'PB'),
        (binary and 'EiB' or 'EB'),
        (binary and 'ZiB' or 'ZB'),
        (binary and 'YiB' or 'YB')
    ]
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
