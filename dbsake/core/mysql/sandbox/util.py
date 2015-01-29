"""
dbsake.core.mysql.sandbox.util
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sandbox utilities
"""
from __future__ import unicode_literals


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
