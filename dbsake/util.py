"""
dbsake.util
~~~~~~~~~~~

Utility methods

"""

import contextlib
import errno
import os
import subprocess

def mkdir_safe(path):
    """mkdir, ignoring errors from existing dirs

    This is a thin wrapper around os.mkdir, but if
    mkdir raises an OSError caused by a directory
    already existing, the error is silently swallowed.
    Other errors are otherwise raised as expected.

    This is similar to os.makedirs(..., exist_ok=True)
    in python 3.2+
    """
    try:
        os.mkdir(path)
    except OSError, exc:
        if exc.errno != errno.EEXIST:
            raise

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

@contextlib.contextmanager
def stream_command(cmd, stdout):
    process = subprocess.Popen(cmd,
                               stdin=subprocess.PIPE,
                               stdout=stdout,
                               shell=True,
                               close_fds=True)
    yield process
    process.stdin.close()
    process.wait()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(cmd, returncode)
