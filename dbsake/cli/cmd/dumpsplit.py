"""
dbsake.cmd.dumsplit
~~~~~~~~~~~~~~~~~~~

Advanced filtering of mysqldump backup files
"""
from __future__ import unicode_literals

import sys

import click

from dbsake.cli import dbsake


@dbsake.command('split-mysqldump')
def split_mysqldump():
    """Filter a mysqldump plaintext SQL stream"""
    click.echo("Unimplemented", file=sys.stderr)
    sys.exit(1)
