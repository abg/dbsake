"""
dbsake.mysql.sandbox.download
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Support for downloading / deploying a binary tarball
"""
from __future__ import print_function, division

import contextlib
import hashlib
import logging
import os
import sys
import time
import urllib2

from . import tarball

info = logging.info
warn = logging.warn
debug = logging.debug

BAR_TEMPLATE = '(%.2f%%)[%s%s] %s/%s\r'

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
        return '1B'
    elif bytes < base:
        return '%dB' % bytes
    else:
        for i, prefix in enumerate(prefixes):
            unit = base ** (i + 2)
            if bytes < unit:
                return '%.1f %s' % ((base * bytes / unit), prefix)
        return '%.1f%s' % ((base * bytes / unit), prefix)


class ResourceProxy(object):
    """
    A proxy for a non-streamable resource that counts bytes and maintains a
    rolling checksum for data read through it.

    Essentially wraps some stream with a read() method, and captures chunks
    from the read to record their length + checksum and returns it to the
    caller.

    TODO: Implement Progress bar feature
          if stderr is a console, we can just write some data to it and hopefully an eta
          in this case we know content-length and we know our current read length so we
          can calculate a percentage very easily.
    TODO: Implement transparent copying to also copy the underlying resource elsewhere
          e.g. something like curl url | tee mysql.tar.gz | tar xf - -C destdir
    """
    def __init__(self, stream, expected_length=0):
        self.stream = stream
        self.checksum = hashlib.md5()
        self.content_length = 0
        self.expected_length = int(expected_length)
        self.last_update = time.time()
        self._finished = False

    def seek(self, *args):
        raise IOError(0, "ResourceProxy does not support seeking")

    def _update_progress(self):
        if self._finished: return
        width = 40
        if (time.time() - self.last_update) > 1 or self.content_length == self.expected_length:
            self.last_update = time.time()
            x = int((self.content_length / self.expected_length)*width)
            pct = (self.content_length / self.expected_length)*100
            sys.stderr.write(
                BAR_TEMPLATE % (pct,
                                '#'*x,
                                ' '*(width - x),
                                format_filesize(self.content_length),
                                format_filesize(self.expected_length)
                                )
            )
            sys.stderr.flush()
        if self.content_length == self.expected_length:
            print(file=sys.stderr)
            self._finished = True

    def read(self, *args):
        chunk = self.stream.read(*args)
        self.content_length += len(chunk)
        self.checksum.update(chunk)
        if os.isatty(sys.stderr.fileno()):
            self._update_progress()
        return chunk

    def __getattr__(self, name):
        return getattr(self.stream, name)

heuristics = {
    '5.0' : dict(
        default='archives/mysql-5.0/mysql-{version}-linux-{arch}-glibc23.tar.gz',
        archive='archives/mysql-5.0/mysql-{version}-linux-{arch}-glibc23.tar.gz',
    ),

    '5.1' : dict(
        default='Downloads/MySQL-5.1/mysql-{version}-linux-{arch}-glibc23.tar.gz',
        archive='archives/mysql-5.1/mysql-{version}-linux-{arch}-glibc23.tar.gz'
    ),

    '5.5' : dict(
        default='Downloads/MySQL-5.5/mysql-{version}-linux2.6-{arch}.tar.gz',
        archive='archives/mysql-5.5/mysql-{version}-linux2.6-{arch}.tar.gz',
    ),

    '5.6' : dict(
        default='Downloads/MySQL-5.6/mysql-{version}-linux-glibc2.5-{arch}.tar.gz',
        archive='archives/mysql-5.6/mysql-{version}-linux-glibc2.5-{arch}.tar.gz'
    ),

    '5.7' : dict(
        default='Downloads/MySQL-5.7/mysql-{version}-linux-glibc2.5-{arch}.tar.gz',
        archive='archives/get/file/mysql-{version}-linux-glibc2.5-{arch}.tar.gz',
    )
}

def stream_tarball(url, destdir):
    name = os.path.basename(url)
    info("Streaming %s from %s", name, url)
    with contextlib.closing(urllib2.urlopen(url)) as request:
        debug("%s: [OK!]" % url)
        etag = request.info()['etag'][1:-1].rpartition(':')[0]
        debug("    etag: %r" % etag)
        content_length = int(request.info()['content-length'])
        debug("    Content-Length: %r" % content_length)
        request.name = name
        stream = ResourceProxy(request, content_length)
        stream.name = name
        tarball.deploy(stream, destdir)
    debug("Final proxy computed checksum: %s" % stream.checksum.hexdigest())
    debug("Final proxy computed length: %s" % stream.content_length)
    if stream.checksum.hexdigest() != etag:
        warn("Warning, checksums don't seem to match")
        warn("%s != %s" % (stream.checksum.hexdigest(), etag))

    if stream.content_length != content_length:
        warn("Read length does not match reported length")
        warn("  %d != %d" % (stream.content_length, content_length))


def download_to(version, destdir):
    # first try normal download

    for method in ('default', 'archive'):
        major_minor = version.rpartition('.')[0]
        url = heuristics[major_minor][method].format(version=version,
                                                     arch='x86_64')
        url = 'http://cdn.mysql.com/' + url
        try:
            return stream_tarball(url, destdir)
        except urllib2.HTTPError as exc:
            if exc.code != 404:
                raise
        except urllib2.URLError as exc:
            # probably something serious went wrong here
            raise
            # otherwise we continue

    # XXX: Consider reraising last 404 error here
    raise LookupError("Could not find the requested MySQL version")
