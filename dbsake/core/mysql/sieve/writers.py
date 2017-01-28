"""
dbsake.core.mysql.sieve.writers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Support for writing mysqldump output.

This API supports two modes for handling mysqldump output:

    - streaming, which is a simple passthrough (possibly transforming or
      filtering data)
    - directory, which splits a single mysqldump stream in a separate
      file per section (possibly transforming or filtering data)
"""
from __future__ import unicode_literals

import itertools
import logging
import os

from dbsake.util import cmd

from . import exc

debug = logging.debug
info = logging.info


class SimpleWriter(object):
    def __init__(self, options, context):
        self.options = options
        self.context = context
        self.stream = options.output_stream

    def __call__(self, section):
        for line in section.iterable:
            self.stream.write(line)


def command_to_ext(command):
    """Given a command like 'gzip --fast' return a filename extension

    >> command_to_ext('lzop -9')
    '.lzo'

    """
    # map base command name to its extension
    known_exts = {
        'gzip': b'.gz',
        'pigz': b'.gz',
        'bzip2': b'.bz2',
        'lbzip2': b'.bz2',
        'pbzip2': b'.bz2',
        'lzop': b'.lzo',
        'xz': b'.xz',
        'lzma': b'.lzma',
    }

    arg0 = cmd.shlex_split(command)[0]
    arg0 = os.path.basename(arg0)

    return known_exts.get(arg0, '')


class DirectoryWriter(SimpleWriter):
    # track the first view, so we can initialize a file as needed
    first_view = False
    replication_info = False

    def _open(self, parts, mode='ab'):
        basedir = self.options.directory.encode('utf8')
        path = os.path.join(basedir, *parts)
        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        if self.options.compress_command:
            ext = command_to_ext(self.options.compress_command)
            path += ext
            return cmd.stream_command(self.options.compress_command,
                                      stdout=open(path, mode))
        else:
            return open(path, mode)

    def open_header(self, section):
        self._dump_header = b''.join(section.iterable)
        return self.open_devnull(section)

    def open_replication_info(self, section):
        if not self.replication_info:
            mode = 'wb'
            self.replication_info = True
        else:
            mode = 'ab'
        return self._open([b'replication_info.sql'], mode=mode)

    def open_createdatabase(self, section):
        return self._open([section.database, section.database + b'.createdb'],
                          mode='wb')

    def open_tablestructure(self, section):
        if self._dump_header:
            section.iterable = itertools.chain([self._dump_header],
                                               section.iterable)
        return self._open([section.database, section.table + b'.sql'],
                          mode='wb')

    def open_tabledata(self, section):
        return self._open([section.database, section.table + b'.sql'],
                          mode='ab')

    def open_triggers(self, section):
        return self._open([section.database, section.table + b'.sql'],
                          mode='ab')

    def open_view(self, section):
        if not self.first_view:
            self.first_view = True
            if self._dump_header:
                section.iterable = itertools.chain([self._dump_header],
                                                   section.iterable)
            mode = 'wb'
        else:
            mode = 'ab'
        return self._open([section.database, b'views.ddl'], mode=mode)

    open_view_temporary = open_view

    def open_routines(self, section):
        if self._dump_header:
            section.iterable = itertools.chain([self._dump_header],
                                               section.iterable)
        return self._open([section.database, b'routines.ddl'], mode='wb')

    def open_events(self, section):
        if self._dump_header:
            section.iterable = itertools.chain([self._dump_header],
                                               section.iterable)
        return self._open([section.database, b'events.ddl'], mode='wb')

    def open_devnull(self, section):
        section.flush()
        return open(os.devnull, 'wb')

    def __call__(self, section):
        try:
            dispatch = getattr(self, 'open_' + section.name)
        except AttributeError:
            # skip output for section
            info("Skipping section '%s'", section.name)
            dispatch = self.open_devnull
        with dispatch(section) as fileobj:
            for line in section.iterable:
                fileobj.write(line)


stream_writer = SimpleWriter
directory_writer = DirectoryWriter


def load(options, context):
    try:
        cls = globals()[options.output_format + '_writer']
    except KeyError:
        raise exc.SieveError("Invalid format '%s'" % options.output_format)

    return cls(options, context)
