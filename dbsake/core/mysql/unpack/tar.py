"""
dbsake.core.mysql.unpack.tar
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Support for unpacking tar files
"""

import contextlib
import tarfile

from dbsake import pycompat

from . import common


def is_tarfile(header):
    if pycompat.PY3:
        extra_args = ('utf8', 'ignore')
    else:
        extra_args = ()
    try:
        tarfile.TarInfo.frombuf(header[0:512], *extra_args)
    except tarfile.TarError:
        return False
    else:
        return True


def entry_extractor(archive, tarinfo):
    """Simple decorator to handle extracting a single entry from a tarfile"""
    def _extract(destination):
        return archive.extract(tarinfo, destination)
    return _extract


def unpack(stream):
    kwargs = dict(fileobj=stream, mode='r|')
    with contextlib.closing(tarfile.open(**kwargs)) as tar:
        for entry in tar:
            path = common.normalize(entry.name).encode('utf-8')
            yield common.Entry(path=path,
                               name=common.qualified_name(path),
                               required=common.is_required(path),
                               chunk=0,
                               extract=entry_extractor(tar, entry))
