"""
dbsake.sandbox.distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Logic for handling different MySQL distribution sources

    Supports:
        Deploying from a locally installed version (e.g. rpm/deb packages already in path)

        Deploying based on a MySQL version - fetched a binary tarball from mysql.com and
        extracts it to the sandbox dir.

Each distribution method should return a SandboxMeta instance that, at a minimum, provides:

    * basedir
    * libexec = path to mysqld
    * mysqld path
    * mysqld_safe
    * mysql (command line client)
    * plugin_dir
"""

import collections
import os
import re
import shutil

from dbsake import sarge
from . import util

# sandbox metadata
# minimum information to setup the sandbox
SandboxMeta = collections.namedtuple('SandboxMeta',
                                     'version mysqld mysqld_safe mysql '
                                     'basedir pkgdatadir libexecdir plugindir')

def mysqld_version(mysqld):
    with sarge.Capture() as stdout:
        cmd = sarge.shell_format('{0} --version', mysqld)
        result = sarge.run(cmd, stdout=stdout)
        if result.returncode != 0:
            raise RuntimeError("Failed to run mysqld --version")
        version_str = stdout.read()
    m = re.search('(\d+[.]\d+[.]\d+)', version_str)
    if not m:
        raise LookupError("Failed to discover version for %s" % cmd)
    return tuple(map(int, m.group(0).split('.')))

def first_subdir(basedir, *paths):
    """Return the first path from ``paths`` that exists under basedir

    """
    for path in paths:
        cpath = os.path.normpath(os.path.join(basedir, path))
        if os.path.exists(cpath):
            return cpath
    return None

def distribution_system(sandbox_directory, **kwargs):
    path = os.pathsep.join(['/usr/libexec', '/usr/sbin', os.environ['PATH']])
    # XXX: abort if any of these weren't found
    mysqld = util.which('mysqld', path=path)
    mysql = util.which('mysql', path=path)
    mysqld_safe = util.which('mysqld_safe', path=path)
    version = mysqld_version(mysqld)
    # XXX: we might be able to look this up from mysqld --help --verbose,
    #      but I really want to avoid that.  This shold cover 99% of local
    #      cases and I think it's fine to abort if this doesn't exist
    basedir = kwargs.pop('basedir', '/usr')
    pkgdatadir = first_subdir(basedir, 'share/mysql', 'share')
    plugindir = first_subdir(basedir, 'lib64/mysql/plugin', 'lib/mysql/plugin')
    
    # now copy mysqld, mysql, mysqld_safe to sandbox_dir/bin
    # then return an appropriate SandboxMeta instance
    bindir = os.path.join(sandbox_directory, 'bin')
    util.mkdir_p(bindir, 0770)
    for path in (mysqld, mysqld_safe, mysql):
        shutil.copy2(path, bindir)

    return SandboxMeta(
        version=version,
        mysqld=os.path.join(bindir, os.path.basename(mysqld)),
        mysqld_safe=os.path.join(bindir, os.path.basename(mysqld_safe)),
        mysql=os.path.join(bindir, os.path.basename(mysql)),
        basedir=basedir,
        pkgdatadir=pkgdatadir,
        libexecdir=bindir,
        plugindir=plugindir
    )

def distribution_tarball(sandbox_directory, path):
    from . import tarball
    with open(path, 'rb') as fileobj:
        tarball.deploy(fileobj, sandbox_directory)
    bindir = os.path.join(sandbox_directory, 'bin')
    version = mysqld_version(os.path.join(bindir, 'mysqld'))

    return SandboxMeta(
        version=version,
        mysqld=os.path.join(bindir, 'mysqld'),
        mysql=os.path.join(bindir, 'mysql'),
        mysqld_safe=os.path.join(bindir, 'mysqld_safe'),
        basedir=sandbox_directory,
        pkgdatadir=os.path.join(sandbox_directory, 'share'),
        libexecdir=bindir,
        plugindir=os.path.join(sandbox_directory, 'lib', 'plugin')
    )

def distribution_version(sandbox_directory, version):
    from . import download
    download.download_to(version, sandbox_directory)

    bindir = os.path.join(sandbox_directory, 'bin')
    version = mysqld_version(os.path.join(bindir, 'mysqld'))

    return SandboxMeta(
        version=version,
        mysqld=os.path.join(bindir, 'mysqld'),
        mysql=os.path.join(bindir, 'mysql'),
        mysqld_safe=os.path.join(bindir, 'mysqld_safe'),
        basedir=sandbox_directory,
        pkgdatadir=os.path.join(sandbox_directory, 'share'),
        libexecdir=bindir,
        plugindir=os.path.join(sandbox_directory, 'lib', 'plugin')
    )
