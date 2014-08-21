"""
dbsake.cmd.fs
~~~~~~~~~~~~~

Commands for interacting with the local filesystem

"""
from __future__ import unicode_literals

import sys

import click

from dbsake.cli import dbsake


@dbsake.command('fincore', options_metavar='[options]')
@click.option('-v', '--verbose', is_flag=True)
@click.argument('paths', nargs=-1, metavar="[path...]")
def fincore(paths, verbose):
    """Report cached pages for a file."""
    from dbsake.core import fs

    errors = 0
    for path in paths:
        try:
            stats = fs.fincore(path, verbose)
            click.echo("%s: total_pages=%d cached=%d percent=%.2f" %
                       (path, stats.total, stats.cached, stats.percent))
        except (IOError, OSError) as exc:
            click.echo("fincore %s failed: %s" % (path, exc))
            errors += 1
            continue
    if errors:
        sys.exit(1)
    else:
        sys.exit(0)


@dbsake.command('uncache', options_metavar='[options]')
@click.argument('paths', nargs=-1, metavar='[path...]')
def uncache(paths):
    """Uncache file(s) from the OS page cache.

    This command calls posix_fadvise(2) to indicate that cached pages for
    a given file are no longer needed.  This is useful when using O_DIRECT
    where cached pages for a given file can lead to a performance
    degradation for many filesystems under Linux.
    """
    from dbsake.core import fs

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
