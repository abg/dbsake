"""
dbsake.util.compression
~~~~~~~~~~~~~~~~~~~~~~~

Access to compression commands

"""

import contextlib
import errno
import os
import stat

from . import cmd
from . import pathutil

# supported compression ext -> command names
COMPRESSION_LOOKUP = {
    '.gz': ('pigz', 'gzip'),
    '.bz2': ('pbzip2', 'bzip2'),
    '.lzo': ('lzop',),
    '.xz': ('xz', 'lzma'),
}

# extension to magic bytes
COMPRESSION_MAGIC = {
    '.gz': b'\x1f\x8b',
    '.bz2': b'BZh',
    '.lzo': b'\x89\x4c\x5a\x4f\x00\x0d\x0a\x1a\x0a',
    '.xz': b'\xFD7zXZ\x00',
}


def ext_to_command(ext):
    """Given a filename extension, find command to decompress it"""
    for name in COMPRESSION_LOOKUP[ext]:
        path = pathutil.which(name)
        if path:
            return path
    raise OSError(errno.ENOENT, "Not found: %s" % name)


@contextlib.contextmanager
def decompressed(path):
    """Open path via a compression command

    """
    ext = os.path.splitext(path)[-1]
    with open(path, 'rb') as stdin:
        with decompressed_fileobj(stdin, ext=ext) as stdout:
            yield stdout


def is_seekable(stream):
    """Determine if a stream is seekable"""
    mode = os.fstat(stream.fileno()).st_mode
    return stat.S_ISREG(mode) != 0


def magic_to_ext(fileobj):
    """Determine compression extension basic on file magic bytes"""
    for ext, expected in COMPRESSION_MAGIC.items():
        fileobj.seek(0)
        magic = fileobj.read(len(expected))
        if magic == expected:
            return ext
    else:
        raise OSError(errno.EIO, "Failed to detect compression type")


@contextlib.contextmanager
def decompressed_fileobj(fileobj, ext=None):
    if ext is None and not is_seekable(fileobj):
        raise OSError("No compression was specified and %s is not seekable.")

    if ext is None:
        ext = magic_to_ext(fileobj)
    command = ext_to_command(ext)
    fd = fileobj.fileno()
    os.lseek(fd, 0, os.SEEK_SET)
    with cmd.piped_stdout("%s -dc" % command, stdin=fd) as stdout:
        yield stdout
