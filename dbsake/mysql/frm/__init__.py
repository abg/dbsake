"""
dbsake.mysql.frm
~~~~~~~~~~~~~~~~

MySQL .frm manipulation utilities

"""
from . import binaryfrm
from . import mysqlview

def parse(path):
    """Parse a .frm file"""
    with open(path, 'rb') as fileobj:
        # read up to 9 bytes to detect a view
        magic = fileobj.read(9)
        if magic.startswith(b'\xfe\x01'):
            parse = binaryfrm.parse
        elif magic == b'TYPE=VIEW':
            parse = mysqlview.parse
        else:
            raise ValueError("Invalid .frm file '%s'" % path)
    return parse(path)
