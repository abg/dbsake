"""
dbsake.mysql.sandbox.distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Support for deploying MySQL distributions

"""

from __future__ import print_function

import collections
import contextlib
import hashlib
import logging
import os
import tarfile
import time
import urllib2
import re
import shutil
import sys

from dbsake.thirdparty import sarge
from dbsake.util import path as dbsake_path

from . import common
from . import util

info = logging.info
debug = logging.debug
warn = logging.warn

class MySQLVersion(collections.namedtuple('MySQLVersion', 'major minor release')):
    def __str__(self):
        return '.'.join(str(part) for part in self)

    @classmethod
    def from_string(cls, value):
        return cls(*map(int, value.split('.')))

MySQLDistribution = collections.namedtuple('MySQLDistribution',
                                           ['version',
                                            'mysqld',
                                            'mysqld_safe',
                                            'mysql',
                                            'basedir',
                                            'sharedir',
                                            'libexecdir',
                                            'plugindir'])

def mysqld_version(mysqld):
    cmd = sarge.shell_format('{0} --version', mysqld)
    result = sarge.capture_both(cmd)
    if result.returncode != 0:
        raise common.SandboxError("Failed to run mysqld --version")
    m = re.search('(\d+[.]\d+[.]\d+)', result.stdout.text)
    if not m:
        raise common.SandboxError("Failed to discover version for %s" % cmd)
    #return tuple(map(int, m.group(0).split('.')))
    return MySQLVersion.from_string(m.group(0))

def first_subdir(basedir, *paths):
    """Return the first path from ``paths`` that exists under basedir

    """
    for name in paths:
        cpath = os.path.normpath(os.path.join(basedir, name))
        if os.path.exists(cpath):
            return cpath
    return None

def deploy(options):
    start = time.time()
    try:
        if options.distribution == 'system':
            return distribution_from_system(options)
        elif os.path.isfile(options.distribution):
            return distribution_from_tarball(options)
        else:
            return distribution_from_download(options)
    finally:
        info("    * Deployed MySQL distribution to sandbox in %.2f seconds", time.time() - start)

def distribution_from_system(options):
    """Deploy a MySQL distribution already installed on the system

    """
    info("    - Deploying MySQL distributed from system binaries")
    envpath = os.pathsep.join(['/usr/libexec', '/usr/sbin', os.environ['PATH']])
    mysqld = dbsake_path.which('mysqld', path=envpath)
    mysql = dbsake_path.which('mysql', path=envpath)
    mysqld_safe = dbsake_path.which('mysqld_safe', path=envpath)

    if None in (mysqld, mysql, mysqld_safe):
        raise common.SandboxError("Unable to find MySQL binaries")
    info("    - Found mysqld: %s", mysqld)
    info("    - Found mysqld_safe: %s", mysqld_safe)
    info("    - Found mysql: %s", mysql)
    version = mysqld_version(mysqld)
    info("    - MySQL server version: %s", version)
    # XXX: we might be able to look this up from mysqld --help --verbose,
    #      but I really want to avoid that.  This shold cover 99% of local
    #      cases and I think it's fine to abort if this doesn't exist
    basedir = '/usr'
    info("    - MySQL --basedir %s", basedir)
    # sharedir is absolutely required as we need it to bootstrap mysql
    # and mysql will fail to start withtout it
    sharedir = first_subdir(basedir, 'share/mysql', 'share')
    if not sharedir:
        raise common.SandboxError("/usr/share/mysql not found")

    info("    - MySQL share found in %s", sharedir)
    # Note: plugindir may be None, if using mysql < 5.1
    plugindir = first_subdir(basedir, 'lib64/mysql/plugin', 'lib/mysql/plugin')
    if plugindir:
        info("    - Found MySQL plugin directory: %s", plugindir)

    # now copy mysqld, mysql, mysqld_safe to sandbox_dir/bin
    # then return an appropriate MySQLDistribution instance
    bindir = os.path.join(options.basedir, 'bin')
    dbsake_path.makedirs(bindir, 0770, exist_ok=True)
    for name in [mysqld]:
        shutil.copy2(name, bindir)
    info("    - Copied minimal MySQL commands to %s", bindir)
    return MySQLDistribution(
        version=version,
        mysqld=os.path.join(bindir, os.path.basename(mysqld)),
        mysqld_safe=mysqld_safe,
        mysql=mysql,
        basedir=basedir,
        sharedir=sharedir,
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

def unpack_tarball_distribution(stream, path):
    debug("    # unpacking tarball stream=%r destination=%r", stream, path)
    tar = tarfile.open(None, 'r|*', fileobj=stream)
    # python 2.6's tarfile does not support the context manager protocol
    # so try...finally is used here
    try:
        for tarinfo in tar:
            if not (tarinfo.isreg() or tarinfo.issym()): continue
            tarinfo.name = os.path.normpath(tarinfo.name)
            name = os.path.join(*tarinfo.name.split(os.sep)[1:])
            item0 = name.split(os.sep)[0]
            if item0 in ('bin', 'lib', 'share', 'scripts'):
                tarinfo.name = name
                #debug("Extracting %s to %s", tarinfo.name, path)
            elif item0 in ('COPYING', 'README', 'INSTALL-BINARY'):
                tarinfo.name = os.sep.join(['docs.mysql', item0])
                #debug("Extracting documentation %s to %s", tarinfo.name, path)
            elif name == 'docs/ChangeLog':
                tarinfo.name = 'docs.mysql/ChangeLog'
                #debug("Extracting Changelog to %s", tarinfo.name)
            else:
                continue
            _fix_tarinfo_user_group(tarinfo)
            tar.extract(tarinfo, path)
    finally:
        tar.close()

def distribution_from_tarball(options):
    """Deploy a MySQL distribution from a binary tarball

    """
    info("    - Deploying distribution from binary tarball: %s", options.distribution)
    with util.StreamProxy(open(options.distribution, 'rb')) as stream:
        if os.isatty(sys.stderr.fileno()):
            size = os.fstat(stream.fileno()).st_size
            stream.add(util.progressbar(max=size))
        unpack_tarball_distribution(stream, options.basedir)

    bindir = os.path.join(options.basedir, 'bin')
    version = mysqld_version(os.path.join(bindir, 'mysqld'))

    info("    - Using mysqld (v%s): %s", version, os.path.join(bindir, 'mysqld'))
    info("    - Using mysqld_safe: %s", os.path.join(bindir, 'mysqld_safe'))
    info("    - Using mysql: %s", os.path.join(bindir, 'mysql'))
    info("    - Using share directory: %s", os.path.join(options.basedir, 'share'))
    info("    - Using mysqld --basedir: %s", options.basedir)
    plugin_dir = os.path.join(options.basedir, 'lib', 'plugin')
    if os.path.exists(plugin_dir):
        info("    - Using MySQL plugin directory: %s", os.path.join(options.basedir, 'lib', 'plugin'))

    return MySQLDistribution(
        version=version,
        mysqld=os.path.join(bindir, 'mysqld'),
        mysql=os.path.join(bindir, 'mysql'),
        mysqld_safe=os.path.join(bindir, 'mysqld_safe'),
        basedir=options.basedir,
        sharedir=os.path.join(options.basedir, 'share'),
        libexecdir=bindir,
        plugindir=os.path.join(options.basedir, 'lib', 'plugin')
    )

class MySQLCDNInfo(collections.namedtuple("MySQLCDNInfo", "name locations")):
    VERSIONS = {
        '5.0' : dict(
            name='mysql-{version}-linux-{arch}-glibc23.tar.gz',
            locations=(
                'archives/mysql-5.0/',
            )
        ),
        '5.1' : dict(
            name='mysql-{version}-linux-{arch}-glibc23.tar.gz',
            locations=(
                'Downloads/MySQL-5.1',
                'archives/mysql-5.1',
            )
        ),
        '5.5' : dict(
            name='mysql-{version}-linux2.6-{arch}.tar.gz',
            locations=(
                'Downloads/MySQL-5.5',
                'archives/mysql-5.5',
            )
        ),
        '5.6' : dict(
            name='mysql-{version}-linux-glibc2.5-{arch}.tar.gz',
            locations=(
                'Downloads/MySQL-5.6',
                'archives/mysql-5.6',
            )
        ),
        '5.7' : dict(
            name='mysql-{version}-linux-glibc2.5-{arch}.tar.gz',
            locations=(
                'Downloads/MySQL-5.7',
                'archives/get/file',
            )
        )
    }

    prefix = 'http://cdn.mysql.com'

    @classmethod
    def from_version(cls, version):
        major_minor = version.rpartition('.')[0]
        try:
            options = cls.VERSIONS[major_minor]
        except KeyError:
            raise common.SandboxError("Version '%s' is unsupported" % version)
        return cls(name=options['name'].format(version=version, arch='x86_64'),
                   locations=options['locations'])

    def __iter__(self):
        for path in self.locations:
            yield '/'.join([self.prefix, path, self.name])

def open_http_download(url):
    try:
        stream = urllib2.urlopen(url)
        # since this from cdn.mysql.com the etag encodes the md5sum
        # this is in "'md5sum:integer'" format
        etag = stream.headers['etag']
        checksum = etag[1:-1].rpartition(':')[0]
        stream.headers['x-dbsake-checksum'] = checksum
        return stream
    except urllib2.HTTPError as exc:
        if exc.code != 404:
            raise common.SandboxError("Failed download: %s" % exc)
        else:
            raise
    except urllib2.URLError as exc:
        raise common.SandboxError("Failed http download: %s" % exc)

def open_cached_download(path):
    # first check md5 information
    checksum = None
    length = None
    try:
        with open(path + '.md5', 'rb') as fileobj:
            for line in fileobj:
                if line.startswith('# size:'):
                    length = line.split()[-1]
                elif line.startswith('#'):
                    continue
                else:
                    checksum = line.split()[0]
    except IOError as exc:
        raise common.SandboxError("Invalid checksum for %s" % path)

    if checksum is None:
        raise common.SandboxError("No valid checksum found for cache file %s" % path)

    try:
        stream = urllib2.urlopen('file://' + path)
        if stream.headers['content-length'] != length:
            stream.close()
            debug("Cache size was not valid. Expected %s bytes found %s",
                  length, stream.headers['content-length'])
            raise common.SandboxError("Invalid cache file %s" % path)
        # set the expected checksum for later validation
        stream.headers['x-dbsake-checksum'] = checksum
        return stream
    except urllib2.URLError as exc:
        raise common.SandboxError("Invalid cache file %s" % path)

def discover_cache_path(name):
    # pull cache directory from environment and default to ~/.dbsake.cache
    cache_directory = os.environ.get('DBSAKE_CACHE', '~/.dbsake/cache')
    cache_path = os.path.join(cache_directory, name)
    # cleanup the cache directory by expanding ~ to $HOME and making
    # any relative paths absolute
    cache_path = os.path.abspath(os.path.expanduser(cache_path))
    # normalize the result - removing redundant directory separators, etc.
    return os.path.normpath(cache_path)

def download_mysql(version, arch, cache_policy):
    cdn = MySQLCDNInfo.from_version(version)
    debug("    # Found MySQL CDN data: %r", cdn)

    cache_path = discover_cache_path(cdn.name)
    stream = None

    if cache_policy not in ('never', 'refresh'):
        # check if a file is in cache
        try:
            stream = open_cached_download(cache_path)
            info("    - Using cached download %s", cache_path)
        except common.SandboxError as exc:
            debug("stream_from_cache failed:", exc_info=True)
            if cache_policy == 'local':
                debug("Aborting. cache-policy = local and no usable cache file")
                raise
            debug("cache-policy allows network fallback, so continuing in spit of no cache")
            # otherwise fall through
            # distribution_from_cache should handle purging cache in this case

    if stream is None:
        debug("Attempting download of MySQL distribution")
        for url in cdn:
            debug(" Trying url: %s", url)
            try:
                stream = open_http_download(url)
                stream.info()['x-dbsake-cache'] = cache_path
                info("    - Downloading from %s", url)
            except urllib2.HTTPError as exc:
                if exc.code != 404:
                    raise common.SandboxError("Failed to download: %s" % exc)
                else:
                    continue
            except urllib2.URLError as exc:
                raise common.SandboxError("Failed to download: %s" % exc)
            else:
                break # stream was opened successfully

    if stream is None:
        raise common.SandboxError("No distribution found")

    if 'x-dbsake-cache' not in stream.info():
        stream.info()['x-dbsake-cache'] = ''
    return util.StreamProxy(stream)

@contextlib.contextmanager
def cache_download(name):
    dbsake_path.makedirs(os.path.dirname(name), exist_ok=True)
    with open(name, 'wb') as fileobj:
        yield fileobj

def check_for_libaio(options):
    """Verify that libaio is available, where necessary

    See http:/bugs.mysql.com/60544 for details of why this check is being done

    """
    version = MySQLVersion.from_string(options.distribution)
    if version < (5, 5, 4):
        return
    info("    - Checking for required libraries...")
    import ctypes.util

    if ctypes.util.find_library("aio") is None:
        msg = "libaio not found - required by MySQL %s" % (version, )
        if options.skip_libcheck:
            warn("    ! %s", msg)
            warn("    ! (continuing anyway due to --skip-libcheck")
        else:
            raise common.SandboxError(msg)

def distribution_from_download(options):
    version = options.distribution # the --mysql-distribution option
    check_for_libaio(options)
    info("    - Attempting to deploy distribution for MySQL %s", version)
    # allow up to 2 attempts - so if the local cache fails we will at least
    # try the network path
    checksum = hashlib.new('md5')
    with download_mysql(version, 'x86_64', options.cache_policy) as stream:
        managers = []
        stream.add(checksum.update)
        if os.isatty(sys.stderr.fileno()):
            stream_size = int(stream.info()['content-length'])
            stream.add(util.progressbar(max=stream_size))
        if options.cache_policy != 'never' and stream.headers['x-dbsake-cache']:
            managers.append(cache_download(stream.headers['x-dbsake-cache']))
            info("    - Caching download: %s", stream.headers['x-dbsake-cache'])
        else:
            debug("    # Not caching download")
        with contextlib.nested(*managers) as ctx:
            if ctx:
                stream.add(ctx[0].write)
                debug("Caching download to %s", ctx[0].name)
            info("    - Unpacking tar stream. This may take some time")
            unpack_tarball_distribution(stream, options.basedir)

    if checksum.hexdigest() != stream.headers['x-dbsake-checksum']:
        warn("    ! Detected checksum error in download")
        warn("    ! Expected MD5 checksum %s but computed %s",
             stream.headers['x-dbsake-checksum'], checksum.hexdigest())
    elif options.cache_policy != 'never' and stream.headers['x-dbsake-cache']:
        cache_path = stream.headers['x-dbsake-cache']
        md5_path = cache_path + '.md5'
        with open(md5_path, 'wb') as fileobj:
            print("# MD5 checksum of cache file", file=fileobj)
            print("# size: %s" % stream.info()['content-length'], file=fileobj)
            print("%s  %s" % (checksum.hexdigest(), cache_path),
                  file=fileobj)
        info("    - Stored MD5 checksum for download: %s", fileobj.name)

    bindir = os.path.join(options.basedir, 'bin')
    version = mysqld_version(os.path.join(bindir, 'mysqld'))

    info("    - Using mysqld (v%s): %s", version, os.path.join(bindir, 'mysqld'))
    info("    - Using mysqld_safe: %s", os.path.join(bindir, 'mysqld_safe'))
    info("    - Using mysql: %s", os.path.join(bindir, 'mysql'))
    info("    - Using share directory: %s", os.path.join(options.basedir, 'share'))
    info("    - Using mysqld --basedir: %s", options.basedir)
    plugin_dir = os.path.join(options.basedir, 'lib', 'plugin')
    if os.path.exists(plugin_dir):
        info("    - Using MySQL plugin directory: %s", os.path.join(options.basedir, 'lib', 'plugin'))

    return MySQLDistribution(
        version=version,
        mysqld=os.path.join(bindir, 'mysqld'),
        mysql=os.path.join(bindir, 'mysql'),
        mysqld_safe=os.path.join(bindir, 'mysqld_safe'),
        basedir=options.basedir,
        sharedir=os.path.join(options.basedir, 'share'),
        libexecdir=bindir,
        plugindir=plugin_dir,
    )
