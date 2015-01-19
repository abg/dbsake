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


def progressbar(max=0, width=20, interval=0.5):
    template = ('{pct:4.0%} {transfer:13s} {rate:6s}/s [{prog:.<{width}}] '
                '{runtime} ETA: {eta}')

    max_size = util.format_filesize(max)
    t0 = time.time()
    metrics = dict(length=0, last_update=0, complete=False)

    def update(data):
        n = len(data)
        metrics['length'] += n
        if time.time() - metrics['last_update'] >= interval or n == 0:
            pct = metrics['length'] / max
            units = int(pct*width)
            n_filesize = util.format_filesize(metrics['length'])[:-1]
            runtime = time.time() - t0
            eta = (max / metrics['length'])*runtime
            rate = util.format_filesize(metrics['length'] / runtime, False)
            runtime_s = time.strftime('%H:%M:%S', time.gmtime(runtime))
            eta_s = time.strftime("%H:%M:%S", time.gmtime(eta))

            pbar = template.format(pct=pct,
                                   transfer='%s/%s' % (n_filesize, max_size),
                                   rate=rate,
                                   prog='='*(units - 1) + '>',
                                   width=width,
                                   runtime=runtime_s,
                                   eta=eta_s)
            end = "\r" if pct < 1 else "\n"
            print(pbar, end=end, file=sys.stderr)
            metrics['last_update'] = time.time()
            sys.stderr.flush()

    return update
