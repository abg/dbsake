"""
dbsake.util.pathutil
~~~~~~~~~~~~~~~~~~~~

Convenience functions for working with filesystem paths
"""

import os


def resolve_mountpoint(path):
    """Discover the mountpoint for the given path

    :param path: starting path
    :returns: mountpoint path string
    """
    path = os.path.realpath(path)

    while path != os.path.sep:
        if os.path.ismount(path):
            return path
        path = os.path.abspath(os.path.join(path, os.pardir))
    return path
