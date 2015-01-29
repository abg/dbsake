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

TABLE_FILE_CRE = re.compile(br'''
^.*[.](frm|isl|ibd|MYD|MYI|MAD|MAI|MRG|TRG|TRN|ARM|ARZ|CSM|CSV|par)$
''', re.VERBOSE)


def normalize(path):
    return os.path.normpath(path)


def qualified_name(path):
    """Extracts and decodes the table and database name from a path

    :returns: qualified database.tablename
    """
    if not TABLE_FILE_CRE.match(path):
        return None

    tbl = os.path.basename(path)
    tbl, _ = os.path.splitext(tbl)
    tbl = tbl.partition(b'#P')[0]
    dbname = os.path.basename(os.path.dirname(path))

    return '%s.%s' % (tablename.decode(dbname),
                      tablename.decode(tbl))


Entry = collections.namedtuple('Entry', 'path name chunk extract')


class UnpackError(Exception):
    """Raised if an error is encountered during an unpack operation"""
