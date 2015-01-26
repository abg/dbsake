"""
dbsake.core.mysql.unpack.common
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Common code between various unpack modules

"""

from __future__ import unicode_literals

import collections
import os
import re

from dbsake.core.mysql.frm import tablename

# File patterns considered "required"
# This includes standard mysql files along with "shared" InnoDB tablespaces
# and Percona XtraBackup control files.
MYSQL_FILE_CRE = re.compile(br'''
    ^mysql_upgrade_info$|       # info written by mysql_upgrade
    ^auto[.]cnf$|               # MySQL 5.6 uuid config
    ^ibdata.*$|                 # InnoDB shared tablespace
    ^ib_logfile.*$|             # InnoDB redo logs
    ^undo.*$|                   # InnoDB undo logs
    ^[^/]+/db[.]opt$|           # database option files
    ^.+[.]tokudb$|              # TokuDB files
    ^tokudb[.].*$|              # TokuDB metadata files
    ^__tokudb_lock.*$|          # TokuDB lock files
    ^log\d+[.]tokulog\d+$|      # TokuDB log files
    ^aria_log.+$|               # Aria log files
    ^backup-my.cnf$|            # Percona XtraBackup backup-my.cnf
    ^xtrabackup.*$|             # Percona XtraBackup data file
    ^mysql/slave_.*$|           # MySQL 5.6 slave info table
    ^mysql/innodb_.*$           # MySQL 5.6 InnoDB system table
''', re.X)


def normalize(path):
    return os.path.normpath(path)


def is_required(path):
    return MYSQL_FILE_CRE.match(path) is not None


def qualified_name(path):
    """Extracts and decodes the table and database name from a path

    :returns: qualified database.tablename
    """
    if MYSQL_FILE_CRE.match(path):
        return None

    tbl = os.path.basename(path)
    tbl, _ = os.path.splitext(tbl)
    tbl = tbl.partition(b'#P')[0]
    dbname = os.path.basename(os.path.dirname(path))

    return '%s.%s' % (tablename.decode(dbname),
                      tablename.decode(tbl))


Entry = collections.namedtuple('Entry', 'path name required chunk extract')


class UnpackError(Exception):
    """Raised if an error is encountered during an unpack operation"""
