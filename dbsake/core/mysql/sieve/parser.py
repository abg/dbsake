"""
dbsake.core.mysql.sieve.parser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parsing support for mysqldump files

This provides an api for reading in a mysqldump stream and returning each
related section as an iterable, while minimizing memory utilization.
"""
from __future__ import unicode_literals

import collections
import logging
import re

try:
    _range = xrange
except NameError:
    _range = range

debug = logging.debug

IDENTIFIER = re.compile(br'''.*?([`'])(?P<ident>.*)\1$''')


def extract_identifier(value):
    m = IDENTIFIER.match(value)
    if not m:
        raise ValueError('No identifier in %r' % value)
    return m.group('ident')

# map line prefixes to identifier names
DISCRIMINATORS = [
    (b'-- MySQL dump', 'header'),
    (b'-- Position', 'replication_info'),
    (b'-- Current Database', 'createdatabase'),
    (b'-- Table structure', 'tablestructure'),
    (b'-- Dumping data for table', 'tabledata'),
    (b'-- Temporary table structure', 'view'),
    (b'-- Dumping routines', 'routines'),
    (b'-- Dumping events', 'events'),
    (b'-- Final view structure', 'view'),
    (b'/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;', 'footer'),
    (b'/*!50003 SET @saved_cs_client', 'triggers'),
    (b'-- Flush Grant Tables', 'flush_privileges'),
    (b'-- Dump completed', 'dump_completed')
]


def discriminate(value):
    for prefix, discriminator in DISCRIMINATORS:
        if value.startswith(prefix):
            break
    else:
        # XXX: need a better exception
        raise ValueError('No match for %r' % value)
    extra = {'name': discriminator}
    if discriminator in ('createdatabase', 'routines', 'events'):
        extra.update(database=extract_identifier(value), table=None)
    elif discriminator in ('tablestructure',
                           'tabledata',
                           'view'):
        extra.update(table=extract_identifier(value))
    elif discriminator == 'flush_privileges':
        extra.update(table=None)
    elif discriminator == 'footer':
        extra.update(database=None, table=None)
    return extra


class Section(object):
    def __init__(self):
        self.name = None
        self.database = None
        self.table = None
        self.iterable = ()

    def flush(self):
        for line in self.iterable:
            pass


class LineReader(object):

    def __init__(self, stream):
        self.stream = stream
        self._cache = collections.deque()

    def __iter__(self):
        return self

    def __next__(self):
        if self._cache:
            line = self._cache.popleft()
        else:
            line = next(self.stream)
        return line
    # python 2.x shim
    next = __next__

    def pushback(self, value):
        self._cache.append(value)

    def expect_prefix(self, prefix):
        line = next(self)
        if not line.startswith(prefix):
            self.pushback(line)
            raise ValueError('Unexpected line: %r' % line)
        return line

    def expect(self, value):
        line = next(self)
        if line.rstrip() != value:
            self.pushback(line)
            raise ValueError('Unexpected line: %r' % line)
        return line

    def expect_blank(self):
        line = next(self)
        if line.rstrip() != b'':
            self.pushback(line)
            raise ValueError('Unexpected line: %r' % line)
        return line

    @property
    def closed(self):
        return self.stream.closed


class DumpParser(object):
    def __init__(self, stream):
        self.section = Section()
        self._stream = LineReader(stream)

    def read_section_header(self):
        yield self._stream.expect_prefix(b'-- MySQL dump')
        yield self._stream.expect_prefix(b'--')
        line = self._stream.expect_prefix(b'-- Host:')
        name = line.rpartition(b'Database: ')[2].rstrip()
        if not name.startswith(b'-- Host:'):
            self.section.database = name
        yield line
        yield self._stream.expect_prefix(b'-- ---')
        yield self._stream.expect_prefix(b'-- Server version')
        yield self._stream.expect_blank()
        # expect a series of /*! lines
        line = self._stream.expect_prefix(b'/*!')
        while line:
            yield line
            try:
                line = self._stream.expect_prefix(b'/*!')
            except ValueError:
                break
        yield self._stream.expect_blank()

    def read_section(self):
        yield self._stream.expect(b'--')
        yield self._stream.expect_prefix(b'-- ')
        yield self._stream.expect(b'--')
        delimiter = False
        for line in self._stream:
            if not delimiter and line.rstrip() == b'--':
                self._stream.pushback(line)
                break
            if line.startswith(b'DELIMITER'):
                delimiter = not delimiter
            elif line.startswith(b'/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;'):
                self._stream.pushback(line)
                break
            yield line

    def read_section_footer(self):
        for line in self._stream:
            yield line

    def read_section_triggers(self):
        delimiter = False
        for line in self._stream:
            if line.startswith(b'DELIMITER ;;'):
                delimiter = True
            if delimiter and line.startswith(b'--\n'):
                self._stream.pushback(line)
                break
            yield line

    def read_section_tabledata(self):
        yield self._stream.expect(b'--')
        yield self._stream.expect_prefix(b'-- ')
        yield self._stream.expect(b'--')
        yield self._stream.expect_blank()
        terminators = (b'/*!',)
        for line in self._stream:
            if line.startswith((b'INSERT', b'REPLACE', b'/*!40000 ALTER')):
                yield line
                continue
            if line.startswith(terminators):
                self._stream.pushback(line)
                break
            yield line
            if line.startswith(b'\n'):
                break

    def discriminate_next(self):
        pending = []
        line = None
        try:
            # assume we can always find the next section in 2 steps:
            # i.e. a '--' + '-- <description>' or '/*!' line that
            # we can use to determine what the next content will be
            # XXX: Need to fix this use of ValueError
            for _ in _range(2):
                line = next(self._stream)
                pending.append(line)
                try:
                    return discriminate(line)
                except ValueError:
                    continue
            raise ValueError('Could not discriminate next section type: %r' %
                             line)
        finally:
            for line in pending:
                self._stream.pushback(line)

    def __iter__(self):
        section = self.section

        while not self._stream.closed:
            discriminator = self.discriminate_next()
            iterable = getattr(self,
                               'read_section_' + discriminator['name'],
                               self.read_section)
            self.section.__dict__.update(discriminator, iterable=iterable())
            yield section
