"""
dbsake.cmd.unpack
~~~~~~~~~~~~~~~~~

Archive unpack cli frontend

"""
from __future__ import print_function
from __future__ import unicode_literals

import sys

import click

from dbsake.cli import dbsake


@dbsake.command('unpack', options_metavar='[options]')
@click.option('-v', '--verbose', is_flag=True)
@click.option('-C', '--directory', default='.')
@click.option('-t', '--table', multiple=True, default=[])
@click.option('-T', '--exclude-table', multiple=True, default=[])
@click.argument('archive', metavar="<path>")
def _unpack(archive, directory, table, exclude_table, verbose):
    """Unpack a MySQL backup archive.

    This command will unpack tar or Percona XtraBackup xbstream
    archives with support for filtering and extracting only a
    subset of tables.

    """
    from dbsake.core.mysql import unpack

    if table:
        table += ('mysql.*',)

    try:
        unpack.unpack(archive, directory, table, exclude_table)
    except unpack.UnpackError as exc:
        print("%s" % exc, file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(0)
