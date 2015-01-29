"""
dbsake.core.mysql.unpack
~~~~~~~~~~~~~~~~~~~~~~~~

Support for unpacking various MySQL datasources

"""
from __future__ import print_function
from __future__ import unicode_literals

import fnmatch
import io
import logging
import re

from dbsake.util import compression

from . import common
from . import tar
from . import xbs

UnpackError = common.UnpackError

debug = logging.debug


def inclusion_exclusion_filter(include=(), exclude=(), mode='glob'):
    """Create an inclusion exclusion filter

    :param include: sequence of regex patterns to include
    :param exclude: sequence of regex patterns to exclude
    :returns: function(name) that filters strings based on the provided filters
    """
    if mode == 'glob':
        re_include = [fnmatch.translate(pat) for pat in include]
        re_exclude = [fnmatch.translate(pat) for pat in exclude]
    elif mode != 'regex':
        raise ValueError("only 'glob' or 'regex' filters are supported")
    else:
        re_include = include
        re_exclude = exclude

    re_include = [re.compile(pat) for pat in re_include]
    re_exclude = [re.compile(pat) for pat in re_exclude]

    def apply_filter(name):
        """Apply a filter to ``name``

        If inclusion patterns are specified and no patterns are
        matched, the value will be excluded and this function
        returns ``True``.

        If no inclusion patterns are specified all values will
        be included unless some exclusion pattern is matched.

        If an exclusion pattern is matched, the matched pattern
        will be returned as true value.

        If no exclusion patterns were matched, ``False`` is returned
        indicating the value was not excluded

        :param name: string value to filter
        :returns: true value if filtered, False otherwise
        """
        if re_include and not any(pat.match(name) for pat in re_include):
            return True
        for idx, pattern in enumerate(re_exclude):
            if pattern.match(name):
                return exclude[idx]
        return False
    return apply_filter


def load_unpacker(stream):
    """Load an unpacker from a binary stream

    BufferedReader.peek() is used to peek at the underlying stream
    to detect the appropriate unpack method.  Stream is expected
    to support the io.BufferedReader interface.

    Currently only tar and xbstream archives are supported.  tar
    archives are used if the first 512 bytes can be decoded via
    tarfile.TarInfo.frombuf(...).  Otherwise, if the first 8 bytes
    match the xbstream magic header 'xbstream' is assumed.

    If no methods are detected, an UnpackError is raised.

    :raises: UnpackError if no suitable unpacker could be found
    :returns: generator yielding Entry instances
    """
    header = stream.peek(512)

    if tar.is_tarfile(header):
        return tar.unpack(stream)
    elif xbs.is_xbstream(header):
        return xbs.unpack(stream)

    raise common.UnpackError("Unknown format for input stream")


def unpack(datasource,
           destination,
           include_tables=(),
           exclude_tables=(),
           report_progress=False,
           list_contents=False):
    """Unpack a MySQL tar or xbstream based datasource

    :param datasource: file object stream to unpack
    :param destination: directory to unpack archive contents to
    :param include_tables: sequence of tables to include (db.tablename)
    :param exclude_tables: sequences of tables to exclude (db.tablename)
    :param report_progress: boolean flag whether to report progress reading
                            stream to stderr

    :raises: UnpackError on error
    """
    name_filter = inclusion_exclusion_filter(include_tables, exclude_tables)

    with compression.decompressed(datasource, report_progress) as stream:
        stream = io.open(stream.fileno(), 'rb', closefd=False)
        for entry in load_unpacker(stream):
            if entry.name is not None and name_filter(entry.name):
                debug("# Skipping: %s" % entry.path)
                continue
            if list_contents:
                if entry.chunk == 0:
                    print(entry.path.decode('utf-8'))
            else:
                entry.extract(destination)
