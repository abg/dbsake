"""
dbsake.core.mysql.sandbox.util
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sandbox utilities
"""
from __future__ import print_function, division

import sys
import time

import dbsake.util as util


class StreamProxy(object):
    """Proxy over an underlying stream

    This class provides a proxy over some sort of streaming file-like object.
    A list of listeners is maintained that are notified on every read() from
    the underlying stream in order to allow multiple sources to do something
    with the data as it is read.
    """
    def __init__(self, stream):
        self.stream = stream
        self._listeners = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    # allow access to arbitrary attributes of underlying stream
    # not otherwise overriden by this proxy
    def __getattr__(self, key):
        return getattr(self.stream, key)

    def add(self, listener):
        """Add a listen to this proxy"""
        self._listeners.append(listener)

    def read(self, *args, **kwargs):
        """Proxy a read to the underlying stream

        This proxies the read to the underlying stream
        and then calls each listener with the chunk read
        """
        chunk = self.stream.read(*args, **kwargs)
        for listener in self._listeners:
            listener(chunk)
        return chunk


def progressbar(max=0, width=40, interval=0.5):
    template = '({pct:6.2%})[{fill:.<{width}}]{cur_size:^10}/{max_size:^10}'
    params = dict(length=0, last_update=0, complete=False)
    max_size = util.format_filesize(max)

    def _show_progress(data):
        params['length'] += len(data)
        if time.time() - params['last_update'] >= interval or \
                (not data and not params['complete']):
            params['last_update'] = time.time()
            frac = params['length'] / max
            units = int(frac*width)
            cur_size = util.format_filesize(params['length'])
            bar = template.format(pct=frac,
                                  fill='='*units,
                                  cur_size=cur_size,
                                  max_size=max_size,
                                  width=width)
            print(bar, end="\r", file=sys.stderr)
            sys.stderr.flush()
        if not data and not params['complete']:
            print(file=sys.stderr)
            params['complete'] = True
    return _show_progress
