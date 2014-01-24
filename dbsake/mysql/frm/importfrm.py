"""
dbsake.mysql.frm.import
~~~~~~~~~~~~~~~~~~~~~~~

Import an .frm file as a MyISAM table

"""

import errno
import os
import struct
import sys

from . import constants
from . import tablename
from . import util


'''
So basically we rewrite the engine flags in the header
    legacy_db_type (offset 0x03) # which storage engine is used for the table
    default_part_type (offset 0x3d) # which storage engine is used for a partition

    Then we jump to the extrainfo section and rewrite the engine and zero out the
    partitioning clause (if any)

'''

def extra_section(data):
    keyinfo_offset = data.uint16_at(0x0006)
    keyinfo_length = data.uint16_at(0x000e)
    if keyinfo_length == 0xffff:
        keyinfo_length = data.uint32_at(0x002f)

    # column defualts section
    defaults_length = data.uint16_at(0x0010)

    # table extra / attributes section
    extrainfo_offset = keyinfo_offset + keyinfo_length + defaults_length
    extrainfo_length = data.uint32_at(0x0037)

    return extrainfo_offset, extrainfo_length

def import_frm(src, dst):
    if os.path.exists(dst):
        raise IOError(errno.EEXIST, "%s already exists. Refusing to overwrite." % dst)
    with open(src, 'rb') as fileobj:
        if fileobj.read(2) != b'\xfe\x01':
            raise IOError(errno.EINVAL, "%s is not a binary .frm file")
        fileobj.seek(0)
        data = util.ByteReader(fileobj.read())
        # keyinfo section

    extra_offset, extra_length = extra_section(data)

    orig_engine = constants.LegacyDBType(data.uint8_at(0x0003)).name
    if orig_engine == 'PARTITION_DB':
        # figure out the actual underlying storage engine is this
        # is a partitioned table
        orig_engine = constants.LegacyDBType(data.uint8_at(0x003d)).name
    # rewrite legacy_db_type
    data.seek(0x0003)
    data.write(b'\x09')
    # rewrite default_part_db_type
    data.seek(0x003d)
    data.write(b'\x00')

    extra_info = util.ByteReader(data.read_at(offset=extra_offset,
                                              size=extra_length))
    
    extra_info.bytes_prefix16()
    # peek at the engine info
    engine_length = extra_info.uint16_at(extra_info.tell())
    if engine_length != len('MyISAM'):
        saved_offset = extra_info.tell()
        # skip over the engine info
        extra_info.bytes_prefix16()
        # read the partition clause
        partition_clause = extra_info.bytes_prefix32()
        extra_info.skip(2)
        remaining = extra_info.read()
        extra_info.seek(saved_offset)
        # write the engine info
        extra_info.write(b'\x06\x00MyISAM')
        # save current offset
        with extra_info.offset(0, os.SEEK_CUR):
            extra_info.write(b'\x00'*(4 + len(partition_clause) + 2 + len(remaining)))
        # zero out the partitioning info
        extra_info.write(b'\x00'*6)
        # append the rest of the extra section
        extra_info.write(remaining)
        # extra_size should shrink by len(partition_clause) + len('MyISAM')
        extra_size = data.uint32_at(0x0037)
        extra_size -= len(partition_clause) + (engine_length - len('MyISAM'))
        data.seek(0x0037)
        data.write(struct.pack('<I', extra_size))
    else:
        extra_info.skip(2)
        extra_info.write(b'MyISAM')
    extra_info.seek(0)
    extra_data = extra_info.read()
    # this should be exactly the same size - we only zero'd out some information
    # in case of removing partitioning
    assert len(extra_data) == extra_length
    data.seek(extra_offset)
    data.write(extra_data)
    
    data.seek(0)
    if os.path.exists(dst):
        raise IOError(errno.EEXIST, "%s already exists. Refusing to overwrite." % dst)
    with open(dst, 'wb') as fileobj:
        fileobj.write(data.read())

    print("Copied %s to %s as MyISAM table" % (src, dst))
    if engine_length != 6:
        print("Note: Partitioning also removed on this table")
    print("Run the follow commands to use this table")
    basename = os.path.splitext(dst)[0]
    name = tablename.filename_to_tablename(basename)
    print("touch %s.MYD" % basename)
    print("chown mysql:mysql %s.*" % basename)
    print("mysql -e 'REPAIR TABLE %s USE_FRM" % name)
    print("ALTER TABLE %s ENGINE=%s" % (name, orig_engine))
