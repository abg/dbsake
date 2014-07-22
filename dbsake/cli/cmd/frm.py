"""
dbsake.cmd.frmdump
~~~~~~~~~~~~~~~~~

Dump schema from MySQL .frm files
"""
from __future__ import unicode_literals

import sys

import click

from dbsake.cli import dbsake


@dbsake.command('frm-to-schema', options_metavar="[options]")
@click.option('-r', '--raw-types', default=False, is_flag=True)
@click.option('-R', '--replace', default=False, is_flag=True)
@click.argument('path',
                type=click.Path(dir_okay=False, resolve_path=True),
                metavar="[path[, path...]]",
                nargs=-1)
def frmdump(path, raw_types, replace):
    """Dump schema from MySQL frm files."""
    from dbsake.mysql import frm

    failures = 0

    for name in path:
        try:
            table = frm.parse(name)
        except frm.Error:
            click.echo("Failed to parse %s" % (name,), file=sys.stderr)
            failures += 1
            continue
        else:
            if table.type == 'VIEW':
                click.echo(table.format(replace))
            else:
                click.echo(table.format(raw_types))
    if failures > 0:
        click.echo("Failed to parse %d paths" % failures, file=sys.stderr)
        sys.exit(1)
    sys.exit(0)

@dbsake.command('filename-to-tablename', options_metavar="[options]")
@click.argument('names', nargs=-1)
def decode(names):
    """Decode a MySQL tablename as a unicode name."""
    from dbsake.mysql.frm import tablename

    for name in names:
        click.echo(tablename.filename_to_tablename(name))

    return 0

@dbsake.command('tablename-to-filename', options_metavar="[options]")
@click.argument('names', nargs=-1)
def encode(names):
    """Encode a MySQL tablename"""
    from dbsake.mysql.frm import tablename

    for name in names:
        click.echo(tablename.tablename_to_filename(name))

    return 0
