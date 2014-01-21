"""
dbsake.mysql.frm
~~~~~~~~~~~~~~~~

MySQL .frm manipulation utilities

"""
from __future__ import print_function

import sys

from dbsake import baker


def parse(path):
    """Parse a .frm file"""
    from . import binaryfrm
    from . import mysqlview
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


@baker.command(name='frm-to-schema')
def frm_to_schema(raw_types=False, replace=False, *paths):
    """Decode a binary MySQl .frm file to DDL

    :param replace: If a path references a view output CREATE OR REPLACE
                    so a view definition can be replaced.
    :param paths: paths to extract schema from
    """
    failures = 0
    for name in paths:
        try:
            table_or_view = parse(name)
            options = {}
            if table_or_view.type == 'VIEW':
                options['create_or_replace'] = replace
            elif table_or_view.type == 'TABLE':
                options['include_raw_types'] = raw_types
            print(table_or_view.format(**options), file=sys.stdout)
        except (ValueError, IOError) as exc:
            print("Failed to parse '%s': %s" % (name, exc), file=sys.stderr)
            failures += 1
            continue

    if failures:
        print("%d parsing failures" % failures)
        return 1
    else:
        return 0

@baker.command(name='filename-to-tablename')
def filename_to_tablename(*names):
    """Decode a MySQL tablename as a unicode name

    :param names: filenames to decode
    """
    from . import tablename
    for name in names:
        print(tablename.filename_to_tablename(name))
    return 0

@baker.command(name='tablename-to-filename')
def tablename_to_filename(*names):
    """Encode a unicode tablename as a MySQL filename

    :param names: names to encode
    """
    from . import tablename
    for name in names:
        print(tablename.tablename_to_filename(name))
    return 0

@baker.command(name='import-frm')
def import_frm(source, destination):
    """Import a binary .frm as a MyISAM table"""
    from . import importfrm
    try:
        importfrm.import_frm(source, destination)
    except IOError as exc:
        print("Import failed: [%d] %s" % (exc.errno, exc.strerror), file=sys.stderr)
        return 1
    else:
        return 0
