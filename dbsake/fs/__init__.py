"""
dbsake.fs
~~~~~~~~~

Filesystem related commands

"""
from __future__ import print_function

import os
import sys

from dbsake import baker

from . import util

@baker.command
def fincore(verbose=False, *paths):
    """Check if a file is cached by the OS

    Outputs the cached vs. total pages with a percent.

    :param verbose: itemize which pages are cached
    :param paths: check if these paths are cached
    """

    if not paths:
        baker.usage('fincore')
        return 1

    errors = 0

    for path in paths:
        try:
            stats = util.fincore(path, verbose)
            for page in stats.pages:
                print("Page %d cached" % page)
            print("%s: total_pages=%d cached=%d percent=%.2f" %
                  (path, stats.total, stats.cached, stats.percent))
        except OSError as exc:
            print("fincore %s failed: %s" % (path, exc))
            errors += 1
            continue
    if errors:
        return 1
    else:
        return 0

@baker.command
def uncache(*paths):
    """Uncache a file from the OS page cache

    :param paths: uncache files for these paths
    """
    # from /usr/include/linux/fadvise.h
    if not paths:
        baker.usage('uncache')
        return 1

    errors = 0
    for path in paths:
        try:
            util.uncache(path)
            print("Uncached %s" % path)
        except (IOError, OSError) as exc:
            print("Could not uncache '%s': [%d] %s" % 
                  (path, exc.errno, exc.strerror),
                  file=sys.stderr)
            errors += 1
    if errors:
        return 1
    else:
        return 0
