"""
dbsake.tests
~~~~~~~~~~~~

Test suite for dbsake
"""

import os

# all timestamps in tst data reference UTC, so we set this here
# XXX: this needs to be handled more cleanly
os.environ['TZ'] = 'UTC'
