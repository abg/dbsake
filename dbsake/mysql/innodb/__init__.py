"""
dbsake.mysql.innodb
~~~~~~~~~~~~~~~~~~~

InnoDB related commands

"""
from . import binlog


class Error(Exception):
    """Raised if error encountered in innodb api"""


def read_innodb_binlog(path):
    """Extract binary log filename/position from ibdata"""
    sys_header = binlog.trx_sysf_get(path)
    try:
        filename, position = binlog.trx_sys_get_mysql_binlog(sys_header)
    except ValueError:
        raise Error("No binary log information was found in '%s'" % path)
        return 1
    return ("CHANGE MASTER TO MASTER_LOG_FILE='%s', MASTER_LOG_POS=%d;" %
            (filename, position))
