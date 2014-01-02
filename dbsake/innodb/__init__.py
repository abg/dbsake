"""
dbsake.innodb
~~~~~~~~~~~~~

InnoDB related commands

"""
from __future__ import print_function
import sys

from dbsake import baker
from . import binlog

@baker.command(name='read-ib-binlog')
def read_innodb_binlog(path):
    """Extract binary log filename/position from ibdata"""
    sys_header = binlog.trx_sysf_get(path)
    try:
        filename, position = binlog.trx_sys_get_mysql_binlog(sys_header)
    except ValueError:
        print("No binary log information was found in '%s'" % path, file=sys.stderr)
        return 1
    print("CHANGE MASTER TO MASTER_LOG_FILE='%s', MASTER_LOG_POS=%d;" % 
          (filename, position))
    return 0
