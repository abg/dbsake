"""
dbsake.cmd.frmdump
~~~~~~~~~~~~~~~~~

Dump schema from MySQL .frm files
"""
import os
import sys

import click

from dbsake.cli import dbsake


def parse_and_print(frm_path, type_codes, replace):
    """Parse the specified .frm path and output

    On failure, emit the failed path on stderr and return
    1 for the failure count.

    On success, emit the frm on stdout and return 0 for the failure count
    """
    from dbsake.core.mysql import frm

    try:
        table = frm.parse(frm_path)
    except frm.Error as exc:
        click.echo("Failed to parse %s: %s" % (frm_path, exc), file=sys.stderr)
        return 1

    if table.type == 'VIEW':
        click.echo(table.format(replace))
    else:
        click.echo(table.format(type_codes))
    return 0


@dbsake.command('frmdump', options_metavar="[options]")
@click.option('-t', '--type-codes',
              default=False,
              is_flag=True,
              help="Show mysql type codes in comments on each column")
@click.option('-r', '--recursive',
              is_flag=True,
              default=False,
              help="Recursively search directories for .frm files.")
@click.option('-R', '--replace',
              default=False,
              is_flag=True,
              help="Output views with CREATE OR REPLACE")
@click.argument('path',
                type=click.Path(dir_okay=True, resolve_path=True),
                metavar="[path...]",
                nargs=-1)
@click.pass_context
def frmdump(ctx, path, recursive, type_codes, replace):
    """Dump schema from MySQL frm files."""
    def _walk_directory(path):
        for dirpath, dirnames, filenames in os.walk(path):
            for name in filenames:
                yield os.path.join(dirpath, name)

    failures = 0
    for name in path:
        if recursive and os.path.isdir(name):
            for subpath in _walk_directory(name):
                if not subpath.endswith('.frm'):
                    continue
                failures += parse_and_print(subpath, type_codes, replace)
        else:
            failures += parse_and_print(name, type_codes, replace)

    if failures > 0:
        click.echo("Failed to parse %d paths" % failures, file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


@dbsake.command('decode-tablename', options_metavar="[options]")
@click.argument('names', nargs=-1, metavar="[name...]")
def decode_tablename(names):
    """Decode a MySQL filename."""
    from dbsake.core.mysql.frm import tablename

    for name in names:
        name = name.encode('utf-8')
        click.echo(tablename.filename_to_tablename(name))

    return 0


@dbsake.command('encode-tablename', options_metavar="[options]")
@click.argument('names', nargs=-1, metavar="[name...]")
def encode_tablename(names):
    """Encode a MySQL table identifier."""
    from dbsake.core.mysql.frm import tablename

    for name in names:
        click.echo(tablename.tablename_to_filename(name))

    return 0
