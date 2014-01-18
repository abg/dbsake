"""
dbsake.mysql.frm.mysqlview
~~~~~~~~~~~~~~~~~~~~~~~~~~

Decode plaintext view .frm files

"""

from __future__ import print_function

import collections
import ConfigParser as configparser
import datetime
import hashlib
import io
import os

from dbsake.util import enum
from . import tablename

# These constants are taken from sql/table.h
# from the MySQL source tree and adapted to python enums here

class ViewAlgorithm(enum.IntEnum):
    """MySQL view ALGORITHM value"""
    UNDEFINED   = 0
    TMPTABLE    = 1
    MERGE       = 2


class ViewSUID(enum.IntEnum):
    """MySQL view SQL SECURITY value"""
    INVOKER = 0
    DEFINER = 1
    DEFAULT = 2


class ViewCheckOption(enum.IntEnum):
    """MySQL view WITH CHECK OPTION value"""
    NONE        = 0
    LOCAL       = 1
    CASCADED    = 2


class MySQLDefiner(collections.namedtuple('MySQLDefiner', 'user host')):
    def __str__(self):
        return "`{0}`@`{1}`".format(self.user, self.host)


class MySQLView(collections.namedtuple('MySQLView',
                                       'name body algorithm definer suid '
                                       'check_option '
                                       'timestamp stored_md5 computed_md5')):

    @property
    def type(self):
        return 'VIEW'

    def format(self, create_or_replace=False):
        header = "\n".join([
            '--',
            '-- View:         {0}'.format(self.name),
            '-- Timestamp:    {0}'.format(self.timestamp),
            '-- Stored MD5:   {0}'.format(self.stored_md5),
            '-- Computed MD5: {0}'.format(self.computed_md5),
            '--',
            '',
            ''
        ])
        parts = []
        if create_or_replace:
            parts.append('CREATE OR REPLACE')
        else:
            parts.append('CREATE')
        parts.append('ALGORITHM=' + self.algorithm.name)
        parts.append('DEFINER=' + str(self.definer))
        security = 'INVOKER' if self.suid.name == 'DEFAULT' else self.suid.name
        parts.append('SQL SECURITY ' + security)
        parts.append('VIEW')
        parts.append("`{0}`".format(self.name))
        parts.append("AS")
        parts.append(self.body)
        if self.check_option:
            parts.append('WITH ' + self.check_option.name + ' CHECK OPTION')
        return header + ' '.join(parts) + ';'


def parse(path):
    """Parse a MySQL .frm view definition

    :raises: ValueError if ``path`` is not a valid view
    :returns: ``View`` instance
    """

    with open(path, 'rb') as fileobj:
        if fileobj.read(9) != b'TYPE=VIEW':
            raise ValueError("'%s' is not a view" % path)
        fileobj.seek(0)
        data = io.BytesIO()
        data.write(b"[view]\n")
        data.write(fileobj.read())
        data.seek(0)
    cfg = configparser.RawConfigParser()
    cfg.readfp(data, path)

    algorithm = ViewAlgorithm(cfg.getint('view', 'algorithm'))
    definer_user = cfg.get('view', 'definer_user').decode('utf8')
    definer_host = cfg.get('view', 'definer_host').decode('utf8')
    suid = ViewSUID(cfg.getint('view', 'suid'))
    name = tablename.decode(os.path.splitext(os.path.basename(path))[0])

    # Safer in 5.1+ when we know the underlying charset
    if cfg.has_option('view', 'view_body_utf8'):
        raw_view_body = cfg.get('view', 'view_body_utf8').decode('string_escape')
        view_body = raw_view_body.decode('utf8')
    else:
        # < 5.1, so assume utf8 if not charset was specified
        raw_view_body = cfg.get('view', 'query').decode('string_escape')
        view_body = raw_view_body.decode('utf8')
            
    check_option = ViewCheckOption(cfg.getint('view', 'with_check_option'))

    md5 = cfg.get('view', 'md5')
    computed_md5 = hashlib.md5()
    computed_md5.update(cfg.get('view', 'query').decode("string_escape"))
    computed_md5 = computed_md5.hexdigest()

    if computed_md5 != md5:
        raise RuntimeError("OMG WTF %r" % path)
    timestamp = datetime.datetime.strptime(cfg.get('view', 'timestamp'),
                                           '%Y-%m-%d %H:%M:%S')

    return MySQLView(
        name=name,
        algorithm=algorithm,
        definer=MySQLDefiner(definer_user, definer_host),
        suid=suid,
        body=view_body,
        check_option=check_option,
        stored_md5=md5,
        computed_md5=computed_md5,
        timestamp=timestamp
    )
