"""
dbsake.util.compression
~~~~~~~~~~~~~~~~~~~~~~~

Access to compression commands

"""

import contextlib
import errno
import os

from . import cmd
from . import pathutil

# supported compression ext -> command names
COMPRESSION_LOOKUP = {
    '.gz': ('pigz', 'gzip'),
    '.bz2': ('pbzip2', 'bzip2'),
    '.lzo': ('lzop',),
    '.xz': ('xz', 'lzma'),
}


def path_to_command(path):
    """Given a path, discover what command should be used to decompress it

    """
    ext = os.path.splitext(path)[1]
    for name in COMPRESSION_LOOKUP[ext]:
        path = pathutil.which(name)
        if path:
            return path
    raise OSError(errno.ENOENT, "Not found: %s" % name)


@contextlib.contextmanager
def decompressed(path):
    """Open path via a compression command

    """
    command = path_to_command(path)
    with open(path, 'rb') as stdin:
        with cmd.piped_stdout("%s -dc" % command, stdin=stdin) as stdout:
            yield stdout
