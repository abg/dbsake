"""
dbsake.core.fs
~~~~~~~~~~~~~~

Support for inspecting and uncaching files from OS cache
"""
from __future__ import division

import collections
import ctypes
import ctypes.util
import os

libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)

# void *mmap(void *addr, size_t length, int prot, int flags,
#            int fd, off_t offset)
mmap = libc.mmap
mmap.argtypes = [
    ctypes.c_void_p,  # void *addr
    ctypes.c_size_t,  # size_t length
    ctypes.c_int,     # int prot
    ctypes.c_int,     # int flags
    ctypes.c_int,     # int fd
    ctypes.c_size_t   # off_t offset
]
mmap.restype = ctypes.c_void_p

# int munmap(void *addr, size_t length)
munmap = libc.munmap
munmap.argtypes = [
    ctypes.c_void_p,  # void *addr
    ctypes.c_size_t,  # size_t length
]
munmap.restype = ctypes.c_int

# int mincore(void *addr, size_t length, unsigned char *vec)
mincore = libc.mincore
mincore.argtypes = [
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.c_void_p,
]
mincore.restype = ctypes.c_int

# int posix_fadvise(int fd, off_t offset, off_t len, int advice)
posix_fadvise = libc.posix_fadvise
posix_fadvise.argtypes = [
    ctypes.c_int,
    ctypes.c_size_t,
    ctypes.c_size_t,
    ctypes.c_int
]
posix_fadvise.restype = ctypes.c_int

# XXX: not correct for at least s390, but ignoring that for now
POSIX_FADV_DONTNEED = 4

PAGESIZE = os.sysconf('SC_PAGE_SIZE')

PROT_READ = 0x1     # /* Page can be read.  */
PROT_WRITE = 0x2     # /* Page can be written.  */
PROT_EXEC = 0x4     # /* Page can be executed.  */
PROT_NONE = 0x0     # /* Page can not be accessed.  */

# (void *) -1 on the current platform
MAP_FAILED = ctypes.c_void_p(-1)
MAP_SHARED = 0x01    # /* Share changes.  */


class CacheStats(collections.namedtuple('CacheStats', 'total cached pages')):
    """Stats for cached pages for a given file

    :attr total: total pages for the file
    :attr cached: number of pages presently cached
    :attr pages: enumerated list of pages
    """
    @property
    def percent(self):
        """Percent of pages that are cached

        Derived property calculated from cached pages divided by total pages.

        If there are no pages (e.g. a zero byte file) then 0 is returned as
        the percent
        """
        if not self.total:
            return 0.0
        else:
            return (self.cached / self.total) * 100.0


def ctypes_os_error(msg):
    """Instantiate an OSError from a ctypes errno

    This is similar to perror(), looking up the errno
    from ctypes and formatting strerror from os.strerror()
    and prefixing that message with the user provided
    message.

    :param msg: msg to to prefix the OSError strerror with
    """
    errno = ctypes.get_errno()
    strerror = os.strerror(errno)
    return OSError(errno, "%s: %s" % (msg, strerror))


def fincore(path, enumerate_pages=False):
    """Check if underlying path is incore

    :returns: CacheStats instance
    """
    with open(path, 'rb') as fileobj:
        st_size = os.fstat(fileobj.fileno()).st_size

        if not st_size:
            return CacheStats(0, 0, ())

        pa = mmap(0, st_size, PROT_NONE, MAP_SHARED, fileobj.fileno(), 0)

        if pa == MAP_FAILED:
            raise ctypes_os_error("mmap('%s')" % path)

        # round the filesize to the nearest page size
        # note the use of integer division here
        total_pages = (st_size+PAGESIZE-1)//PAGESIZE

        try:
            vec = (ctypes.c_uint8*total_pages)()
            ret = mincore(ctypes.c_void_p(pa), ctypes.c_size_t(st_size), vec)
            if ret != 0:
                raise ctypes_os_error("mincore")
        finally:
            ret = munmap(ctypes.c_void_p(pa), ctypes.c_size_t(st_size))
            if ret != 0:
                raise ctypes_os_error("munmap")

        cached_count = 0
        cached_count = sum(1 for page in vec if page & 1)
        pages = ()
        if enumerate_pages:
            pages = tuple(offset
                          for offset, page in enumerate(vec)
                          if page & 1)
        return CacheStats(total_pages, cached_count, pages)


def uncache(path):
    """Uncache the file contents specified by ``path``

    :param path: the path to uncache
    :raises: OSError, IOError
    """
    with open(path, 'rb') as fileobj:
        ret = posix_fadvise(fileobj.fileno(), 0, 0, POSIX_FADV_DONTNEED)
        if ret != 0:
            raise ctypes_os_error("posix_fadvise")
