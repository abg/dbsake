"""
dbsake.innodb.binlog
~~~~~~~~~~~~~~~~~~~~

Read innodb binlog information from a shared tablespace

"""
import os
import struct
import sys

## InnoDB constants

#: size of an innodb page
# (defined in include/univ.i)
UNIV_PAGE_SIZE = 16384

#: The offset of the transaction system header on the page
TRX_SYS = 38

#: transactin system header page
# (found in include/trx0sys.h)
TRX_SYS_PAGE_NO = 5

#: The offset of the MySQL binlog offset info in the trx system header
TRX_SYS_MYSQL_LOG_INFO = UNIV_PAGE_SIZE - 1000

#: magic number which is TRX_SYS_MYSQL_LOG_MAGIC_N if we have valid data in
#: the MySQL binlog info
TRX_SYS_MYSQL_LOG_MAGIC_N_FLD = 0

#: Contents of TRX_SYS_MYSQL_LOG_MAGIC_N_FLD
TRX_SYS_MYSQL_LOG_MAGIC_N = 873422344

#: high 4 bytes of the offset within that file
TRX_SYS_MYSQL_LOG_OFFSET_HIGH = 4

#: low 4 bytes of the offset within that file
TRX_SYS_MYSQL_LOG_OFFSET_LOW = 8

#: Maximum length of MySQL binlog file name, in bytes
TRX_SYS_MYSQL_LOG_NAME_LEN = 512

#: MySQL log file name
TRX_SYS_MYSQL_LOG_NAME = 12

## InnoDB methods

# adapated from include/trx0sys.ic:trx_sysf_get
def trx_sysf_get(ibdata_path):
    """Retrieve the system header page from given file

    :param ibdata_path: Path the ibdata system tablespace file
                        (usually $datadir/ibdata1)
    :returns: system header page
    """
    # XXX: assert fileobj space_id == 0
    fileobj = open(ibdata_path, 'rb')
    fileobj.seek(UNIV_PAGE_SIZE*TRX_SYS_PAGE_NO)
    sys_header = fileobj.read(UNIV_PAGE_SIZE)
    fileobj.close()
    return sys_header[TRX_SYS:]

# adapted from trx_sys_update_mysql_binlog_offset in trx/trx0sys.c
def trx_sys_get_mysql_binlog(sys_header):
    """Retrieve the mysql binlog file and position from the system header
    page

    :param sys_header: system header page provided by trx_sysf_get
    :returns: mysql_binlog_path (str), mysql_binlog_pos (int)
    """
    offset = TRX_SYS_MYSQL_LOG_INFO + TRX_SYS_MYSQL_LOG_MAGIC_N_FLD
    magic, = struct.unpack('>I', sys_header[offset:offset+4])
    if magic != TRX_SYS_MYSQL_LOG_MAGIC_N:
        raise ValueError("InnoDB MySQL Log magic does not match "
                         "%s != (expected) %s" %
                         (magic, TRX_SYS_MYSQL_LOG_MAGIC_N))


    #offset = TRX_SYS_MYSQL_LOG_INFO + TRX_SYS_MYSQL_LOG_OFFSET_HIGH
    #trx_sys_mysql_bin_log_pos_high, = unpack('>I', sys_header[offset:offset+4])

    #offset = TRX_SYS_MYSQL_LOG_INFO + TRX_SYS_MYSQL_LOG_OFFSET_LOW
    #trx_sys_mysql_bin_log_pos_low, = unpack('>I', sys_header[offset:offset+4])

    #trx_sys_mysql_bin_log_pos = (trx_sys_mysql_bin_log_pos_high << 32) + \
    #                            trx_sys_mysql_bin_log_pos_low

    offset = TRX_SYS_MYSQL_LOG_INFO + TRX_SYS_MYSQL_LOG_OFFSET_HIGH
    mysql_binlog_pos, = struct.unpack('>Q', sys_header[offset:offset+8])
    offset = TRX_SYS_MYSQL_LOG_INFO + TRX_SYS_MYSQL_LOG_NAME
    mysql_binlog_name = sys_header[offset:offset + TRX_SYS_MYSQL_LOG_NAME_LEN]
    mysql_binlog_name = mysql_binlog_name.rstrip(b'\x00').decode('utf8')
    return mysql_binlog_name, mysql_binlog_pos
