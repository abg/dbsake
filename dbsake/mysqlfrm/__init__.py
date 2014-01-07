"""
dbsake.mysqlfrm
~~~~~~~~~~~~~~~

MySQL .frm manipulation utilities

"""
from __future__ import print_function

import itertools
import sys

from dbsake import baker

from . import importfrm
from . import parser
from . import mysqlview
from . import tablename

@baker.command(name='frm-to-schema')
def frm_to_schema(raw_types=False, replace=False, *paths):
    """Decode a binary MySQl .frm file to DDL

    :param replace: If a path references a view output CREATE OR REPLACE
                    so a view definition can be replaced.
    :param paths: paths to extract schema from
    """
    def _fmt_column(column):
        value = str(column)
        if raw_types:
            value += ' /* MYSQL_TYPE_%s */' % column.type_code.name
        return value

    failures = 0
    for name in paths:
        try:
            with open(name, 'rb') as fileobj:
                header = fileobj.read(9)
        except IOError as exc:
            print("Unable to open '%s': [%d] %s" % (name, exc.errno, exc.strerror), file=sys.stderr)
            failures += 1
            continue

        try:
            if header[0:2] == b'\xfe\x01':
                table = parser.parse(name)
                g = itertools.chain((_fmt_column(c) for c in table.columns),
                                     table.keys)
                print("--")
                print("-- Table structure for table `%s`" % table.name)
                print("-- Created with MySQL Version {0}".format(table.mysql_version))
                print("--")
                print()
                print("CREATE TABLE `%s` (" % table.name)
                print(",\n".join("  %s" % str(name) for name in g))
                print(") {0};".format(table.options))
                print()
            elif header == b'TYPE=VIEW':
                view = mysqlview.parse(name)
                table = str(view)
                if replace:
                    table = table.replace('CREATE', 'CREATE OR REPLACE', 1)
                print(table)
                print()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            exc = sys.exc_info()[1]
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
    for name in names:
        print(tablename.filename_to_tablename(name))
    return 0

@baker.command(name='tablename-to-filename')
def tablename_to_filename(*names):
    """Encode a unicode tablename as a MySQL filename

    :param names: names to encode
    """
    for name in names:
        print(tablename.tablename_to_filename(name))
    return 0

@baker.command(name='import-frm')
def import_frm(source, destination):
    """Import a binary .frm as a MyISAM table"""
    try:
        importfrm.import_frm(source, destination)
    except IOError as exc:
        print("Import failed: [%d] %s" % (exc.errno, exc.strerror), file=sys.stderr)
        return 1
    else:
        return 0
