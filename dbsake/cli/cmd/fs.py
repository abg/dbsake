"""
dbsake.cmd.fs
~~~~~~~~~~~~

Commands for interacting with the local filesystem

"""
from __future__ import unicode_literals

import sys

import click

from dbsake.cli import dbsake


@dbsake.command()
@click.option('-v', '--verbose', is_flag=True)
@click.argument('paths', nargs=-1)
def fincore(paths, verbose):
    """Report cached pages for a file."""
    from dbsake import fs

    errors = 0
    for path in paths:
        try:
            stats = fs.fincore(path, verbose)
            click.echo("%s: total_pages=%d cached=%d percent=%.2f" %
                       (path, stats.total, stats.cached, stats.percent))
        except OSError as exc:
            click.echo("fincore %s failed: %s" % (path, exc))
            errors += 1
            continue
    if errors:
        sys.exit(1)
    else:
        sys.exit(0)
        

@dbsake.command()
@click.argument('paths', nargs=-1)
def uncache(paths):
    """Drop OS cached pages for a file."""
    from dbsake import fs

    errors = 0
    for path in paths:
        try:
            fs.uncache(path)
            click.echo("Uncached %s" % path)
        except (IOError, OSError) as exc:
            click.echo("Failed to uncache %s: [%d] %s" %
                       (path, exc.errno, exc.strerror),
                       file=sys.stderr)
            errors += 1
    if errors:
        sys.exit(1)
    else:
        sys.exit(0)
