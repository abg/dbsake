"""
dbsake.util.compression
~~~~~~~~~~~~~~~~~~~~~~

Access to compression commands

"""
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import contextlib
import io
import os
import stat
import sys
import threading
import time

from . import cmd
from . import fmt

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


def is_seekable(stream):
    """Determine if a stream is seekable"""
    mode = os.fstat(stream.fileno()).st_mode
    return stat.S_ISREG(mode) != 0


def rate_bar():
    """Create a new rate bar

    This computes how many bytes have passed through it and the
    rate its received bytes, but does not show progress as it
    has no information about the total number of bytes.
    """
    start = time.time()
    ctx = {'nbytes': 0}

    template = '{elapsed:>9s} {rate:>7s}/s {transferred:>7s} copied'

    def update(ndelta):
        """Update the number of bytes and output a new progress bar"""
        nbytes = ctx['nbytes'] + ndelta
        ctx['nbytes'] = nbytes
        runtime = time.time() - start
        end = "\r" if ndelta != 0 else "\n"
        barstr = template.format(
            elapsed=fmt.timespan(runtime),
            rate=fmt.filesize(nbytes/runtime),
            transferred=fmt.filesize(nbytes)
        )
        print(barstr, end=end, file=sys.stderr)
    return update


def progress_bar(maxsize, width=25):
    """Create a progressbar to measure progress to some maximum size

    """
    start = time.time()
    ctx = {'nbytes': 0}
    samples = []

    template = ('{pct:<6s} [{prog:.<{width}}] '
                '{rate:>7s}/s {transferred:>15s} '
                '{elapsed:<9s} ETA:{eta:<9s} ')

    def update(n):
        """Update the progress bar"""
        nbytes = ctx['nbytes'] + n
        ctx['nbytes'] = nbytes

        elapsed = time.time() - start
        if not samples:
            samples.extend([(nbytes, elapsed)]*10)
        samples.append((nbytes, elapsed))
        pct = nbytes/maxsize
        eta = elapsed*(maxsize / nbytes) - elapsed
        nbytes1, elapsed1 = samples.pop(0)
        if nbytes > nbytes1:
            etasamp = ((elapsed - elapsed1)*(maxsize - nbytes1) /
                       (nbytes - nbytes1) - (elapsed - elapsed1))
            weight = (nbytes / maxsize)**0.5
            eta = (1 - weight)*eta + weight*etasamp
        transferred = fmt.filesize(nbytes) + '/' + fmt.filesize(maxsize)
        barstr = template.format(
            elapsed=fmt.timespan(elapsed),
            eta=fmt.timespan(eta),
            pct='{0:4.1%}'.format(nbytes/maxsize),
            rate=fmt.filesize(nbytes/elapsed),
            transferred=transferred,
            prog='='*int(pct*(width - 1)) + '>',
            width=width
        )
        end = "\r" if n != 0 else "\n"
        print(barstr, end=end, file=sys.stderr)
    return update


class ProxyStream(threading.Thread):
    def __init__(self,
                 stream,
                 widget=None,
                 interval=0.5,
                 block_size=io.DEFAULT_BUFFER_SIZE):
        super(ProxyStream, self).__init__()
        self.stream = stream
        self.widget = widget
        self.interval = interval
        rd, wr = os.pipe()
        self.rd = rd
        self.wr = os.fdopen(wr, 'wb')
        self.block_size = block_size
        self.daemon = True

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        os.close(self.rd)
        self.join()
        self.wr.close()

    def fileno(self):
        return self.rd

    def run(self):
        widget = self.widget
        interval = self.interval
        read = self.stream.read
        write = self.wr.write
        block_size = self.block_size
        last_update = 0
        n = 0

        try:
            block = read(block_size)
            while block:
                write(block)
                if widget:
                    n += len(block)
                    now = time.time()
                    if (now - last_update) > interval:
                        widget(n)
                        last_update = now
                        n = 0
                block = read(block_size)
            if widget:
                widget(n)
                widget(0)
        finally:
            self.wr.close()


def detect_filetype(fileobj):
    """Detect the compression type for the file stream

    This requires fileobj to be of type BufferedReader, so that the
    first few bytes can be peeked at to detect known magic values
    for compression.

    If magic values are detected this method will return the expected
    extension type that can be fed into ``filetype_to_command`` to
    generate a commandline that would decompress this stream.

    If no magic value is matched, this method returns 'None'.

    :param fileobj: io.BufferedReader instance
    :returns: extension string, if found otherwise None
    """

    prefix = fileobj.peek(512)

    for ext, magic in COMPRESSION_MAGIC.items():
        if prefix.startswith(magic):
            return ext

    return None


def filetype_to_command(ext):
    """Given a filetype extensions, return a commandline for decompression

    :param ext: compression extension
    :returns: commandline to decompress or None if an unknown compression
              method is detected.
    """
    zcmds = {
        '.gz': ('pigz', 'gzip'),
        '.bz2': ('pbzip2', 'bzip2', 'lbzip2'),
        '.lzo': ('lzop',),
        '.xz': ('pxz', 'xz')
    }

    if ext in zcmds:
        return zcmds[ext][0] + ' -dc'
    else:
        return None


@contextlib.contextmanager
def decompressed(stream, report_progress=False, sizehint=None, filetype=None):
    """Context manager to decompress a stream of bytes.

    Note: This method will convert a stream to an io.BufferedReader() instance
          and peek at the first few bytes, if filetype is not provided. The
          original stream should not be used afterwards, because its position
          will be in an undefined state.

    :param stream: input stream to decompress
    :param report_progress: bool flag to indicate whether progress reads from
                            the streaming will be emitted to sys.stderr.
    :param sizehint: (optional) integer value to indicate the expected size of
                     the stream.  If not provided and the underlying stream
                     does not provide os.fstat().st_size information, progress
                     will only show transfer rate + bytes transferred but no
                     eta related information.
    :param filetype: (optional) string indicating the filetype of the stream
                     This should be a compression extension:
                     .gz, .bz2, .lzo, .xz
                     If not provided, it will be looked up.
    """
    # convert to a BufferedReader
    # note: closefd=False because we assume called is managing stream lifetime
    #       if this code closes the stream, a future fileobj.close() will
    #       fail with an EBADF as python tries to flush a closed file object.
    #       This causes a very confusing and difficult to debug error
    if filetype is None:
        stream = io.open(stream.fileno(), 'rb', closefd=False)
        filetype = detect_filetype(stream)
    command = filetype_to_command(filetype)
    if report_progress and (sizehint or is_seekable(stream)):
        streamsize = sizehint or os.fstat(stream.fileno()).st_size
        widget = progress_bar(streamsize)
    elif report_progress:
        widget = rate_bar()
    else:
        widget = None

    if filetype is not None:
        with ProxyStream(stream, widget) as fileobj:
            with cmd.piped_stdout(command, stdin=fileobj) as output:
                yield output
    else:
        yield stream
