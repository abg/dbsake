"""
dbsake.util.compression
~~~~~~~~~~~~~~~~~~~~~~~

Access to compression commands

"""
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import contextlib
import errno
import os
import stat
import sys
import threading
import time

from dbsake import pycompat

from . import cmd

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
        path = pycompat.which(name)
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
        os.lseek(fileobj.fileno(), 0, os.SEEK_SET)
    command = ext_to_command(ext)
    with cmd.piped_stdout("%s -dc" % command, stdin=fileobj) as stdout:
        yield stdout


class PVProxy(threading.Thread):
    def __init__(self, source, block_size=8192, total_bytes=None):
        super(PVProxy, self).__init__()
        self.daemon = True
        self.block_size = block_size
        self.source = source
        rd, wr = os.pipe()
        self.pipe_rd = rd
        self.pipe_wr = os.fdopen(wr, 'wb')
        self.bytes_read = 0

        src_st = os.fstat(source.fileno())
        if total_bytes is None and stat.S_ISREG(src_st.st_mode):
            self.total_bytes = src_st.st_size
        else:
            self.total_bytes = total_bytes
        self.t0 = time.time()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print(file=sys.stderr)
        try:
            os.close(self.fileno())
        except OSError:
            pass
        try:
            self.pipe_wr.close()
        except IOError:
            pass

    def progress_bar(self):
        if self.total_bytes is not None:
            return self.eta
        else:
            return self.rate

    def rate(self, n):
        print("Total bytes read: %s" % self.bytes_read)

    def eta(self):
        from dbsake.util import format_filesize

        tpl = ('{pct:4.0%} {transfer:13s} {rate:6s}/s [{prog:.<{width}}] '
               '{runtime} ETA: {eta}')

        pct = self.bytes_read / self.total_bytes
        runtime = time.time() - self.t0
        eta = (self.total_bytes / self.bytes_read)*runtime
        copied = format_filesize(self.bytes_read, False).replace("B", "")
        total = format_filesize(self.total_bytes, False).replace("B", "")
        rate = format_filesize(self.bytes_read / runtime, False)
        runtime_s = time.strftime('%H:%M:%S', time.gmtime(runtime))
        eta_s = time.strftime("%H:%M:%S", time.gmtime(eta))
        width = 20  # width of the progress bar -> 1 unit = ~5% progress

        pbar = tpl.format(pct=pct,
                          transfer='%s/%s' % (copied, total),
                          rate=rate,
                          prog='='*(int(pct*width) - 1) + '>',
                          width=width,
                          runtime=runtime_s,
                          eta=eta_s)
        end = "\r" if pct < 1 else "\n"
        print(pbar, end=end, file=sys.stderr)

    def fileno(self):
        return self.pipe_rd

    def run(self):
        progress_bar = self.progress_bar()
        block = self.source.read(self.block_size)
        last = None
        while block:
            try:
                self.pipe_wr.write(block)
            except IOError:
                print(file=sys.stderr)
                block = ''
                continue
            n = len(block)
            self.bytes_read += n
            if not last or time.time() - last >= 0.25:
                progress_bar()
                last = time.time()
            block = self.source.read(self.block_size)
        progress_bar()
        try:
            self.pipe_wr.close()
        except IOError:
            pass


@contextlib.contextmanager
def decompressed_w_progress(path):
    with open(path, 'rb') as srcf:
        ext = magic_to_ext(srcf)
        srcf.seek(0)
        with PVProxy(srcf) as proxyf:
            with decompressed_fileobj(proxyf, ext=ext) as stdout:
                yield stdout
