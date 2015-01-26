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
@click.option('-l', '--list-contents', 'list_contents', is_flag=True,
              help="List the contents of the archive, but don't extract.")
@click.option('--progress/--no-progress', 'report_progress',
              default=sys.stderr.isatty(),
              help="Enable/disable progress bar when unpacking.")
@click.option('-C', '--directory', metavar='<path>',
              default='.',
              help="Directory to output to (default: $PWD)")
@click.option('-t', '--table', multiple=True, metavar='<db.table>',
              default=[],
              help="Only extract table datafiles matching specified " +
                   "database.table glob patterns.")
@click.option('-T', '--exclude-table', multiple=True, metavar='<db.table>',
              default=[],
              help="Exclude table data files matching specified " +
                   "databsae.table glob patterns.")
@click.argument('archive', metavar="<path>",
                default="-",
                type=click.File('rb'))
def _unpack(archive, list_contents, directory, table, exclude_table, report_progress):
    """Unpack a MySQL backup archive.

    This command will unpack tar or Percona XtraBackup xbstream
    archives with support for filtering and extracting only a
    subset of tables.

    """
    from dbsake.core.mysql import unpack

    if archive.fileno() == 0 and sys.stdin.isatty():
        print("Refusing to read stdin from console.", file=sys.stderr)
        print("Please redirect stdin or specified the archive to unpack.",
              file=sys.stderr)
        sys.exit(1)

    if table:
        table += ('mysql.*',)

    try:
        unpack.unpack(archive, directory,
                      list_contents=list_contents,
                      include_tables=table,
                      exclude_tables=exclude_table,
                      report_progress=report_progress)
    except unpack.UnpackError as exc:
        print("%s" % exc, file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(0)
