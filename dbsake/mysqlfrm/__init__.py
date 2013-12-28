"""
dbsake.mysqlfrm
~~~~~~~~~~~~~~~

MySQL .frm manipulation utilities

"""
from __future__ import print_function

import itertools

from dbsake import baker

from . import parser

@baker.command(name='frm-to-schema')
def frm_to_schema(*paths):
    for name in paths:
        try:
            table = parser.parse(name)
        except IOError as exc:
            print >>sys.stderr, "Could not parse '%s': [%d] %s" % (name, exc.errno, exc.strerror)
            return 1

        g = itertools.chain(table.columns, table.keys)

        print("--")
        print("-- Created with MySQL Version {0}".format(table.mysql_version))
        print("--")
        print()
        print("CREATE TABLE `%s` (" % table.name)
        print(",\n".join("  %s" % str(name) for name in g))
        print(") {0};".format(table.options))
    return 0
