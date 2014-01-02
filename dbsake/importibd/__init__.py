"""
dbsake.importibd
~~~~~~~~~~~~~~~~

Import an .ibd tablespace using MySQL 5.6 transportable tablespace feature

"""
from __future__ import print_function

import sys

from dbsake import baker

#@baker.command(name='import-ibd')
def importibd():
    print("Not implemented.", file=sys.stderr)
    return 1
