"""
dbsake.core.mysql.frm
~~~~~~~~~~~~~~~~~~~~~

MySQL .frm manipulation utilities

"""
from __future__ import unicode_literals

from . import binaryfrm
from . import mysqlview


class Error(Exception):
    """Base error type when an issue occurs parsing an .frm"""


def parse(path):
    """Parse a .frm file

    :param path: path to a .frm file. path may be either a binary .frm or a
                 view
    :returns: Table or View instance
    """
    if not path.endswith('.frm'):
        raise Error("%s does not appear to be a .frm file" % path)

    try:
        with open(path, 'rb') as fileobj:
            # read up to 9 bytes to detect a view
            magic = fileobj.read(9)
            if magic.startswith(b'\xfe\x01'):
                dispatch = binaryfrm.parse
            elif magic == b'TYPE=VIEW':
                dispatch = mysqlview.parse
            else:
                raise Error("Invalid .frm file '%s'" % path)
    except IOError as exc:
        raise Error("Failed to read '%s': %s [%d]" %
                    (exc.filename, exc.strerror, exc.errno))
    return dispatch(path)
