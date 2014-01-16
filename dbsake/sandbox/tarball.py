"""
dbsake.sandbox.tarball
~~~~~~~~~~~~~~~~~~~~~~

Support for deploying from a binary tarball

"""

import logging
import os
import tarfile

debug = logging.debug
info  = logging.info

def _fix_tarinfo_user_group(tarinfo):
    # this only matters if we're already root
    # and we don't want user/group settings to
    # carry over from whatever weird value was
    # in the tarball
    # default to mysql:mysql - and fallback to
    # root:root (0:0) if necessary
    tarinfo.uname = 'mysqmysqll'
    tarinfo.gname = 'mysql'
    tarinfo.uid = 0
    tarinfo.gid = 0

def deploy(stream, destdir):
    """Deploy a MySQL binary tarball distribution to destdir

    :param stream: underlying file-like object that represents
                   the tarball
    :param destdir: directory to extract the tarblal to
    """
    tar = tarfile.open(None, mode='r|gz', fileobj=stream)
    for tarinfo in tar:
        # skip anything that's not a regular file
        if not tarinfo.isreg(): continue
        debug("archive member: %s", tarinfo.name)
        # skip leading directory
        name = os.path.join(*tarinfo.name.split(os.sep)[1:])
        item0 = name.split(os.sep)[0]
        _fix_tarinfo_user_group(tarinfo)
        if item0 in ('bin', 'lib', 'share', 'scripts'):
            tarinfo.name = name
            debug("Extracting %s to %s", tarinfo.name, destdir)
            tar.extract(tarinfo, destdir)
        elif item0 in ('COPYING', 'README', 'INSTALL-BINARY'):
            tarinfo.name = os.sep.join(['docs.mysql', item0])
            debug("Extracting documentation %s to %s", tarinfo.name, destdir)
            tar.extract(tarinfo, destdir)
        elif name == 'docs/ChangeLog':
            tarinfo.name = 'docs.mysql/ChangeLog'
            debug("Extracting Changelog to %s", tarinfo.name)
            tar.extract(tarinfo, destdir)
        # otherwise the archive member is skipped over if it's not
        # a part of one of the above whitelist rules
