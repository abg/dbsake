"""
dbsake.core.mysql.unpack.xbs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

xbstream is one of the archive formats supported by Percona
XtraBackup and this module supports unpacking the format
similar to tar archives.
"""
from __future__ import print_function
from __future__ import unicode_literals

import collections
import errno
import logging
import os
import struct
import zlib

from . import common


class XBSChunk(collections.namedtuple('XBSChunk',
                                      'flags type path payload offset')):
    """Represent a single chunk in an XBS archive."""
    def eof(self):
        return self.type == b'E'


XBS_MAGIC = b"XBSTCK01"

XBS_HEADER_SIZE = 8 + 1 + 1 + 4


def is_xbstream(header):
    """Determine if a file seems to be an xbstream archive

    This currently only checks that the first 8 bytes are
    the "magic" number for xbstream.

    :returns: True if an xbstream archive, False otherwise
    """
    return header.startswith(XBS_MAGIC)


def read_xbs_chunk(stream):
    """Read one chunk from the underlying xbstream file object

    :param stream: a file-like object
    :returns: XBSChunk instance
    """
    header = stream.read(XBS_HEADER_SIZE)
    if not header:
        # end of stream
        return None

    magic, flags, _type, pathlen = struct.unpack(b'<8sBcI', header)

    if magic != XBS_MAGIC:
        raise common.UnpackError("Incorrect magic '%s' in chunk" % magic)

    path = stream.read(pathlen)

    if _type == b'E':
        return XBSChunk(flags, _type, path, b'', None)
    elif _type != b'P':
        raise common.UnpackError("Unknown chunk type '%r'" % _type)

    payload_length, payload_offset = struct.unpack(b'<QQ', stream.read(16))
    checksum, = struct.unpack(b'<I', stream.read(4))
    payload = stream.read(payload_length)

    computed_checksum = zlib.crc32(payload) & 0xffffffff

    if checksum != computed_checksum:
        raise common.UnpackError("Invalid checksum(offset=%d path=%s)" %
                                 (payload_offset, path))

    return XBSChunk(flags, _type, path, payload, payload_offset)


def unpack(stream):
    """Unpack an Percona XtraBackup xbstream archive.

    :raises: UnpackError on error
    :yields: unpack.Entry for each chunk in stream
    """
    # track currently open files
    files = {}

    def extractor(chunk):
        def _extract(destination):
            try:
                dstf = files[chunk.path]
            except KeyError:
                path = os.path.join(destination.encode('utf-8'), chunk.path)
                pardir = os.path.dirname(path)
                try:
                    os.makedirs(pardir)
                    logging.debug("Created directory: %s", pardir)
                except OSError as exc:
                    if exc.errno != errno.EEXIST:
                        raise
                dstf = open(path, 'wb')
                files[chunk.path] = dstf
            if chunk.payload:
                dstf.seek(chunk.offset)
                dstf.write(chunk.payload)
        return _extract

    chunk = read_xbs_chunk(stream)
    while chunk:
        path = common.normalize(chunk.path)
        yield common.Entry(path=path,
                           name=common.qualified_name(path),
                           chunk=chunk.offset is not None,
                           extract=extractor(chunk))
        if chunk.eof() and chunk.path in files:
            files[chunk.path].close()
            del files[chunk.path]
        chunk = read_xbs_chunk(stream)
