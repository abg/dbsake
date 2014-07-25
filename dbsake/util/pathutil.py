"""
dbsake.util.pathutil
~~~~~~~~~~~~~~~~~~~~

Convenience functions for working with filesystem paths
"""

import collections
import errno
import os
import sys


_ntuple_diskusage = collections.namedtuple('usage', 'total used free')


def disk_usage(path):
    """Return disk usage statistics about the given path.

    Return value is a named tuple with attributes 'total', 'used' and
    'free', which are the amount of total, used and free space, in bytes.
    """
    stv = os.statvfs(resolve_mountpoint(path))
    free = stv.f_bavail * stv.f_frsize
    total = stv.f_blocks * stv.f_frsize
    used = (stv.f_blocks - stv.f_bfree) * stv.f_frsize
    return _ntuple_diskusage(total, used, free)


def makedirs(name, mode=0o777, exist_ok=False):
    """makedirs(path [, mode=0o777][, exist_ok=False])

    Dispatch to os.makedirs and suppress an EEXIST error if the
    leaf path exists and exist_ok is True

    :returns: True if a directory was created, else False
    """
    try:
        os.makedirs(name, mode)
        return True
    except OSError as exc:
        if exc.errno != errno.EEXIST or not exist_ok:
            raise
        return False


# backport from py2.7.  patched to support paths relative to /
def relpath(path, start=os.curdir):
    """Return a relative version of a path"""
    sep = os.sep
    curdir = os.curdir
    pardir = os.pardir
    commonprefix = os.path.commonprefix
    abspath = os.path.abspath
    join = os.path.join

    if not path:
        raise ValueError("no path specified")

    start_list = [x for x in abspath(start).split(sep) if x]
    path_list = [x for x in abspath(path).split(sep) if x]

    # Work out how much of the filepath is shared by start and path.
    i = len(commonprefix([start_list, path_list]))

    rel_list = [pardir] * (len(start_list)-i) + path_list[i:]
    if not rel_list:
        return curdir
    return join(*rel_list)


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


def which(cmd, mode=os.F_OK | os.X_OK, path=None):
    """Given a command, mode, and a PATH string, return the path which
    conforms to the given mode on the PATH, or None if there is no such
    file.

    `mode` defaults to os.F_OK | os.X_OK. `path` defaults to the result
    of os.environ.get("PATH"), or can be overridden with a custom search
    path.

    """
    def _access_check(filename, mode):
        """
        Check that a given file can be accessed with the correct mode.
        Additionally check that `file` is not a directory, as on Windows
        directories pass the os.access check.
        """
        return (os.path.exists(filename) and os.access(filename, mode)
                and not os.path.isdir(filename))

    # If we're given a path with a directory part, look it up directly rather
    # than referring to PATH directories. This includes checking relative to
    # the current directory, e.g. ./script
    if os.path.dirname(cmd):
        if _access_check(cmd, mode):
            return cmd
        return None

    if path is None:
        path = os.environ.get("PATH", os.defpath)
    if not path:
        return None
    path = path.split(os.pathsep)

    if sys.platform == "win32":  # pragma: no cover
        # The current directory takes precedence on Windows.
        if os.curdir not in path:
            path.insert(0, os.curdir)

        # PATHEXT is necessary to check on Windows.
        pathext = os.environ.get("PATHEXT", "").split(os.pathsep)
        # See if the given file matches any of the expected path extensions.
        # This will allow us to short circuit when given "python.exe".
        # If it does match, only test that one, otherwise we have to try
        # others.
        if any(cmd.lower().endswith(ext.lower()) for ext in pathext):
            files = [cmd]
        else:
            files = [cmd + ext for ext in pathext]
    else:
        # On other platforms you don't have things like PATHEXT to tell you
        # what file suffixes are executable, so just pass on cmd as-is.
        files = [cmd]

    seen = set()
    for dirpath in path:
        normdir = os.path.normcase(dirpath)
        if normdir not in seen:
            seen.add(normdir)
            for thefile in files:
                name = os.path.join(dirpath, thefile)
                if _access_check(name, mode):
                    return name
    return None
