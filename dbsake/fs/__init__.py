"""
dbsake.fs
~~~~~~~~~

Filesystem related commands

"""
from __future__ import print_function, division

import ctypes
import ctypes.util
import os
import sys

try:
    _range = xrange
except NameError:
    _range = range

from dbsake import baker

# some constants we obtain from the mmap module
from mmap import MAP_SHARED, PAGESIZE
# locate libc
libc = ctypes.CDLL(ctypes.util.find_library("c"))
#XXX: Attribute error is raise if these aren't defined
mmap = libc.mmap
mmap.restype = ctypes.c_void_p
mincore = libc.mincore
PROT_NONE = 0x0
MAP_FAILED = -1

@baker.command
def fincore(verbose=False, *paths):
    for path in paths:
        with open(path, 'rb') as fileobj:
            fd = fileobj.fileno()
            st_size = os.fstat(fd).st_size
            # pa = mmap((void *)0, st.st_size, PROT_NONE, MAP_SHARED, fd, 0);
            pa = mmap(ctypes.c_void_p(0),
              ctypes.c_size_t(st_size),
              ctypes.c_int(PROT_NONE),
              ctypes.c_int(MAP_SHARED),
              ctypes.c_int(fd),
              ctypes.c_size_t(0))
            if pa == -1:
                print("mmap of '%s' failed." % path, file=sys.stderr)
                return 1
            allocsize = (st_size+PAGESIZE-1)//PAGESIZE
            vec = (ctypes.c_uint8*allocsize)()
            ret = mincore(ctypes.c_void_p(pa), ctypes.c_size_t(st_size), vec)
            if ret != 0:
                printf("mincore failed.")
                return 1

            cached_count = 0
            total_pages = st_size//PAGESIZE
            for page_no in _range(st_size//PAGESIZE):
                if vec[page_no] & 1:
                    if verbose:
                        print("Page %d is cached" % page_no)
                    cached_count += 1
            pct_cached = (cached_count / total_pages)*100
            print("%d cached pages of %d total pages (%.3f%%)" % (cached_count, total_pages, pct_cached))
    return 0

@baker.command
def uncache(verbose=False, *paths):
    # from /usr/include/linux/fadvise.h
    POSIX_FADV_DONTNEED = 4
    libc = ctypes.CDLL(ctypes.util.find_library("c"))
    posix_fadvise = libc.posix_fadvise
    errors = 0

    for path in paths:
        try:
            with open(path, 'rb') as fileobj:
                ret = posix_fadvise(fileobj.fileno(), 0, 0, POSIX_FADV_DONTNEED)
                if ret != 0:
                    print("posix_fadvise(%s) failed (ret=%d)" % (path, ret), file=sys.stderr)
                    errors += 1
                elif verbose:
                    print("Uncached %s" % path)
        except IOError as exc:
            print("Could not uncache '%s': [%d] %s" % (path, exc.errno, exc.strerror), file=sys.stderr)
            errors += 1
    return errors and 1 or 0
