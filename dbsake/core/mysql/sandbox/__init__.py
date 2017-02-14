"""
dbsake.core.mysql.sandbox
~~~~~~~~~~~~~~~~~~~~~~~~~

MySQL sandboxing support

"""
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import getpass
import logging
import os
import time

from dbsake import pycompat
from dbsake.util import format_filesize
from dbsake.util import pathutil

from . import common
from . import datasource
from . import distribution

info = logging.info
error = logging.error

# expose SandboxError here as a front-end API
SandboxError = common.SandboxError


def create(**options):
    info("Checking sandbox options")
    sbopts = common.check_options(**options)

    # a basic sanity check: make sure there's at least 1GB free (or 5%)
    usage = pycompat.disk_usage(pathutil.resolve_mountpoint(sbopts.basedir))

    if usage.free < 1024**3:
        raise SandboxError(("Only {0} of {1} (<{2:.2%}) available on {3}. "
                           "Aborting.").format(
                           format_filesize(usage.free),
                           format_filesize(usage.total),
                           usage.free / usage.total,
                           pathutil.resolve_mountpoint(sbopts.basedir)))

    start = time.time()
    sbdir = sbopts.basedir

    info("Preparing sandbox instance: %s", sbdir)
    info("  Creating sandbox directories")
    common.prepare_sandbox_paths(sbopts)
    # Note here that loading from mysqldump sources cannot be done
    # until after the sandbox is bootstrapped
    # And generating defaults cannot be done until we have an
    # innodb-log-file-size
    datasource.preload(sbopts)
    info("  Deploying MySQL distribution")
    dist = distribution.deploy(sbopts)
    info("  Generating my.sandbox.cnf")
    common.generate_defaults(sbopts,
                             mysql_user=sbopts.mysql_user,
                             password=sbopts.password,
                             system_user=getpass.getuser(),
                             distribution=dist,
                             basedir=dist.basedir,
                             datadir=sbopts.datadir,
                             socket=os.path.join(sbopts.datadir, 'mysql.sock'),
                             tmpdir=os.path.join(sbdir, 'tmp'),
                             mysql_version=dist.version,
                             port=dist.version.as_int())
    info("  Bootstrapping sandbox instance")
    common.bootstrap(sbopts, dist)
    info("  Creating sandbox.sh initscript")
    common.generate_initscript(sbdir,
                               distribution=dist,
                               datadir=sbopts.datadir,
                               defaults_file=os.path.join(sbdir,
                                                          'my.sandbox.cnf'))

    info("  Initializing database user")
    common.initialize_mysql_user(sbopts)

    info("Sandbox created in %.2f seconds", time.time() - start)
    info("")
    info("Here are some useful sandbox commands:")
    info("       Start sandbox: %s/sandbox.sh start", sbdir)
    info("        Stop sandbox: %s/sandbox.sh stop", sbdir)
    info("  Connect to sandbox: %s/sandbox.sh mysql <options>", sbdir)
    info("   mysqldump sandbox: %s/sandbox.sh mysqldump <options>", sbdir)
    info("Install SysV service: %s/sandbox.sh install-service", sbdir)
