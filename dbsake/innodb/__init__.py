"""
dbsake.innodb
~~~~~~~~~~~~~

InnoDB related commands

"""
from __future__ import print_function

from dbsake import baker
from . import binlog

@baker.command(name='read-ib-binlog')
def read_innodb_binlog(path):
    sys_header = binlog.trx_sysf_get(path)
    filename, position = binlog.trx_sys_get_mysql_binlog(sys_header)
    print("CHANGE MASTER TO MASTER_LOG_FILE='%s', MASTER_LOG_POS=%d;" % 
          (filename, position))
    return 0
