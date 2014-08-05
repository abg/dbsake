"""
dbsake.cmd.frmdump
~~~~~~~~~~~~~~~~~

Dump schema from MySQL .frm files
"""
from __future__ import unicode_literals

import sys

import click

from dbsake.cli import dbsake


@dbsake.command('frmdump', options_metavar="[options]")
@click.option('-t', '--type-codes',
              default=False,
              is_flag=True,
              help="Show mysql type codes in comments on each column")
@click.option('-R', '--replace',
              default=False,
              is_flag=True,
              help="Output views with CREATE OR REPLACE")
@click.argument('path',
                type=click.Path(dir_okay=False, resolve_path=True),
                metavar="[path...]",
                nargs=-1)
def frmdump(path, type_codes, replace):
    """Dump schema from MySQL frm files."""
    from dbsake.core.mysql import frm

    failures = 0

    for name in path:
        try:
            table = frm.parse(name)
        except frm.Error as exc:
            click.echo("Failed to parse %s: %s" % (name, exc), file=sys.stderr)
            failures += 1
            continue
        else:
            if table.type == 'VIEW':
                click.echo(table.format(replace))
            else:
                click.echo(table.format(type_codes))
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
