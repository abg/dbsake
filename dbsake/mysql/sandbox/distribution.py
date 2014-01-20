"""
dbsake.mysql.sandbox.distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
import contextlib
import hashlib
import logging
import os
import re
import shutil
import sys
import tarfile
import urllib2

from dbsake.thirdparty import sarge
from dbsake.util import path

from . import util

debug = logging.debug
info = logging.info
warn = logging.warn

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
    for name in paths:
        cpath = os.path.normpath(os.path.join(basedir, name))
        if os.path.exists(cpath):
            return cpath
    return None

def deploy(options):
    if options.distribution == 'system':
        return distribution_from_system(options)
    elif os.path.isfile(options.distribution):
        return distribution_from_tarball(options)
    else:
        return distribution_from_network(options)

def distribution_from_system(options):
    envpath = os.pathsep.join(['/usr/libexec', '/usr/sbin', os.environ['PATH']])
    # XXX: abort if any of these weren't found
    mysqld = path.which('mysqld', path=envpath)
    mysql = path.which('mysql', path=envpath)
    mysqld_safe = path.which('mysqld_safe', path=envpath)
    version = mysqld_version(mysqld)
    # XXX: we might be able to look this up from mysqld --help --verbose,
    #      but I really want to avoid that.  This shold cover 99% of local
    #      cases and I think it's fine to abort if this doesn't exist
    basedir = '/usr'
    pkgdatadir = first_subdir(basedir, 'share/mysql', 'share')
    plugindir = first_subdir(basedir, 'lib64/mysql/plugin', 'lib/mysql/plugin')
    
    # now copy mysqld, mysql, mysqld_safe to sandbox_dir/bin
    # then return an appropriate SandboxMeta instance
    bindir = os.path.join(options.basedir, 'bin')
    path.makedirs(bindir, 0770, exist_ok=True)
    for name in (mysqld, mysqld_safe, mysql):
        shutil.copy2(name, bindir)

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

def _fix_tarinfo_user_group(tarinfo):
    # this only matters if we're already root
    # and we don't want user/group settings to
    # carry over from whatever weird value was
    # in the tarball
    # default to mysql:mysql - and fallback to
    # root:root (0:0) if necessary
    tarinfo.uname = 'mysql'
    tarinfo.gname = 'mysql'
    tarinfo.uid = 0
    tarinfo.gid = 0

def _extract_tarball_distribution(stream, basedir):
    with tarfile.open(None, 'r|*', fileobj=stream) as tar:
        for tarinfo in tar:
            if not tarinfo.isreg(): continue
            tarinfo.name = os.path.normpath(tarinfo.name)
            name = os.path.join(*tarinfo.name.split(os.sep)[1:])
            item0 = name.split(os.sep)[0]
            _fix_tarinfo_user_group(tarinfo)
            if item0 in ('bin', 'lib', 'share', 'scripts'):
                tarinfo.name = name
                debug("Extracting %s to %s", tarinfo.name, basedir)
            elif item0 in ('COPYING', 'README', 'INSTALL-BINARY'):
                tarinfo.name = os.sep.join(['docs.mysql', item0])
                debug("Extracting documentation %s to %s", tarinfo.name, basedir)
            elif name == 'docs/ChangeLog':
                tarinfo.name = 'docs.mysql/ChangeLog'
                debug("Extracting Changelog to %s", tarinfo.name)
            else:
                continue
            tar.extract(tarinfo, basedir)

def distribution_from_tarball(options):
    with open(options.distribution, 'rb') as stream:
        _extract_tarball_distribution(stream, options.basedir)

    bindir = os.path.join(options.basedir, 'bin')
    version = mysqld_version(os.path.join(bindir, 'mysqld'))

    return SandboxMeta(
        version=version,
        mysqld=os.path.join(bindir, 'mysqld'),
        mysql=os.path.join(bindir, 'mysql'),
        mysqld_safe=os.path.join(bindir, 'mysqld_safe'),
        basedir=options.basedir,
        pkgdatadir=os.path.join(options.basedir, 'share'),
        libexecdir=bindir,
        plugindir=os.path.join(options.basedir, 'lib', 'plugin')
    )

DIST_URLS = {
    '5.0' : dict(
        default='archives/mysql-5.0/mysql-{version}-linux-{arch}-glibc23.tar.gz',
        archive='archives/mysql-5.0/mysql-{version}-linux-{arch}-glibc23.tar.gz',
    ),

    '5.1' : dict(
        default='Downloads/MySQL-5.1/mysql-{version}-linux-{arch}-glibc23.tar.gz',
        archive='archives/mysql-5.1/mysql-{version}-linux-{arch}-glibc23.tar.gz'
    ),

    '5.5' : dict(
        default='Downloads/MySQL-5.5/mysql-{version}-linux2.6-{arch}.tar.gz',
        archive='archives/mysql-5.5/mysql-{version}-linux2.6-{arch}.tar.gz',
    ),

    '5.6' : dict(
        default='Downloads/MySQL-5.6/mysql-{version}-linux-glibc2.5-{arch}.tar.gz',
        archive='archives/mysql-5.6/mysql-{version}-linux-glibc2.5-{arch}.tar.gz'
    ),

    '5.7' : dict(
        default='Downloads/MySQL-5.7/mysql-{version}-linux-glibc2.5-{arch}.tar.gz',
        archive='archives/get/file/mysql-{version}-linux-glibc2.5-{arch}.tar.gz',
    )
}

def _download_url(version, location='default'):
    try:
        path = DIST_URLS[version][location]
    except KeyError:
        raise # XXX: raise a SandboxError here
    return 'http://cdn.mysql.com/' + path
 
def _stream_tarball(url, basedir, cache_policy):
    with contextlib.closing(urllib2.urlopen(url)) as stream:
        headers = stream.info()
        etag = headers['etag']
        stored_digest = etag[1:-1].partition(':')[0]
        content_length = int(headers['content-length'])

        with util.StreamProxy(stream) as proxy:
            checksum = hashlib.new('md5')
            proxy.add(checksum.update)
            if os.isatty(sys.stderr.fileno()):
                proxy.add(util.progressbar(max=content_length))
            managers = []
            if cache_policy != 'never':
                managers.append(util.cache_url(url))
            with contextlib.nested(*managers) as ctx:
                if ctx:
                    proxy.add(ctx[0].write)
                _extract_tarball_distribution(proxy, basedir)
    if checksum.hexdigest() != stored_digest:
        warn("Calculated tarball digest does not match etag")
        warn("%s != %s", checksum.hexdigest(), stored_digest)

def distribution_from_network(options):
    cachedir = os.path.expanduser('~/.dbsake/cache')
    major_minor = options.distribution.rpartition('.')[0]
    for location in ('default', 'archive'):
        url = _download_url(major_minor, location).format(
                version=options.distribution,
                arch='x86_64',
              )
        info("Trying url: %s", url)
        try:
            with open(os.path.join(cachedir, os.path.basename(url)), 'rb') as stream:
                info("Found cache file '%s'. Attempting extraction", stream.name)
                with util.StreamProxy(stream) as proxy:
                    proxy.add(util.progressbar(max=os.stat(stream.name).st_size))
                    _extract_tarball_distribution(proxy, options.basedir)
                break
        except IOError:
            info("Cache invalid or not found", exc_info=True)
            info("Trying download")

        try:
            _stream_tarball(url, options.basedir, options.cache_policy)
            break
        except urllib2.HTTPError as exc:
            if exc.code != 404:
                raise
        except urllib2.URLError as exc:
            raise
    else:
        raise LookupError("No such distribution found") # XXX: raise sandbox error

    bindir = os.path.join(options.basedir, 'bin')
    version = mysqld_version(os.path.join(bindir, 'mysqld'))

    return SandboxMeta(
        version=version,
        mysqld=os.path.join(bindir, 'mysqld'),
        mysql=os.path.join(bindir, 'mysql'),
        mysqld_safe=os.path.join(bindir, 'mysqld_safe'),
        basedir=options.basedir,
        pkgdatadir=os.path.join(options.basedir, 'share'),
        libexecdir=bindir,
        plugindir=os.path.join(options.basedir, 'lib', 'plugin')
    )
