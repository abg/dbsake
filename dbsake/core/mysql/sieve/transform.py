"""
dbsake.core.mysql.sieve.transform
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

API for transforming mysqldump sections
"""

import itertools

from . import defer

SKIP_BINLOG = b'/*!40101 SET @OLD_SQL_LOG_BIN=@@SQL_LOG_BIN, SQL_LOG_BIN=0 */;'
ENABLE_BINLOG = b'/*!40101 SET SQL_LOG_BIN=@OLD_SQL_LOG_BIN */;'


class SectionTransform(object):
    def __init__(self, options):
        self.options = options
        # used to track deferred keys / constraints
        # in order to output them after the data load
        self.pending_ddl = None

    def transform_header(self, section):
        if not self.options.write_binlog:
            # add a SET SQL_LOG_BIN = 0 in header
            section.iterable = list(section.iterable)
            section.iterable.insert(-1, SKIP_BINLOG + b'\n')

    def transform_footer(self, section):
        if not self.options.write_binlog:
            # add a SET SQL_LOG_BIN = 1 in footer
            section.iterable = list(section.iterable)
            section.iterable.insert(-2, ENABLE_BINLOG + b'\n')

    def transform_replication_info(self, section):
        data = b''.join(section.iterable)
        # explit True / False tests are done here
        # so that we leave replication info alone if no option was
        # explicitly passed by the user
        if self.options.master_data is True:
            data = data.replace(b'-- CHANGE MASTER', b'CHANGE MASTER')
        elif self.options.master_data is False:
            data = data.replace(b'CHANGE MASTER', b'-- CHANGE MASTER')
        section.iterable = data.splitlines(True)

    def transform_tablestructure(self, section):
        defer_indexes = self.options.defer_indexes
        defer_fks = self.options.defer_foreign_keys

        if defer_indexes:
            alter_table = defer.split_indexes(section, defer_fks)
            self.pending_ddl = itertools.chain(alter_table.splitlines(True),
                                               [b'\n', b'\n'])

    def transform_tabledata(self, section):
        if self.pending_ddl:
            section.iterable = itertools.chain(section.iterable,
                                               self.pending_ddl)
            self.pending_ddl = None

    def __call__(self, section):
        try:
            dispatch = getattr(self, 'transform_' + section.name)
        except AttributeError:
            pass
        else:
            dispatch(section)
