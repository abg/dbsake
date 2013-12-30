"""
dbsake.mysqlfrm
~~~~~~~~~~~~~~~

MySQL .frm manipulation utilities

"""
from __future__ import print_function

import codecs
import itertools
import sys

from dbsake import baker

from . import parser
from . import tablename

@baker.command(name='frm-to-schema')
def frm_to_schema(*paths):
    failures = 0
    for name in paths:
        try:
            table = parser.parse(name)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            exc = sys.exc_info()[1]
            print("Failed to parse '%s': %s" % (name, exc), file=sys.stderr)
            failures += 1
            continue

        stdout = codecs.getwriter('utf8')(sys.stdout)
        g = itertools.chain(table.columns, table.keys)
        print("--", file=stdout)
        print("-- Created with MySQL Version {0}".format(table.mysql_version), file=stdout)
        print("--", file=stdout)
        print(file=stdout)
        print("CREATE TABLE `%s` (" % table.name, file=stdout)
        print(",\n".join("  %s" % str(name) for name in g), file=stdout)
        print(") {0};".format(table.options), file=stdout)
        print(file=stdout)
    
    if failures:
        print("%d parsing failures" % failures)
        return 1
    else:
        return 0

@baker.command(name='filename-to-tablename')
def filename_to_tablename(*names):
    """Convert a MySQL filename to a unicode tablename"""
    for name in names:
        print(tablename.filename_to_tablename(name))
    return 0

@baker.command(name='tablename-to-filename')
def tablename_to_filename(*names):
    for name in names:
        print(tablename.tablename_to_filename(name))
    return 0
