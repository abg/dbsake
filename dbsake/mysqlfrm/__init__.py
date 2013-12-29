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

@baker.command(name='frm-to-schema')
def frm_to_schema(*paths):
    for name in paths:
        try:
            table = parser.parse(name)
        except IOError as exc:
            print("Could not parse '%s': [%d] %s" % (name, exc.errno, exc.strerror), file=sys.stderr)
            return 1
        except:
            print("Failed at name=%r" % name)
            raise

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
    return 0
