"""
dbsake.sandbox.download
~~~~~~~~~~~~~~~~~~~~~~~

Support for downloading / deploying a binary tarball
"""
from __future__ import print_function

import contextlib
import hashlib
import logging
import os
import time
import urllib2

from . import tarball

info = logging.info
warn = logging.warn
debug = logging.debug

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
    def __init__(self, stream):
        self.stream = stream
        self.checksum = hashlib.md5()
        self.content_length = 0
        self.last_update = time.time()

    def seek(self, *args):
        raise IOError(0, "ResourceProxy does not support seeking")

    def read(self, *args):
        chunk = self.stream.read(*args)
        self.content_length += len(chunk)
        self.checksum.update(chunk)
        if time.time() - self.last_update > 2:
            self.last_update = time.time()
            debug("%s bytes downloaded" % self.content_length)
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
}

def stream_tarball(url, destdir):
    name = os.path.basename(url)
    info("Streaming %s from %s", name, url)
    with contextlib.closing(urllib2.urlopen(url)) as request:
        debug("%s: [OK!]" % url)
        stream = ResourceProxy(request)
        etag = request.info()['etag'][1:-1].rpartition(':')[0]
        debug("    etag: %r" % etag)
        content_length = int(request.info()['content-length'])
        debug("    Content-Length: %r" % content_length)
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
