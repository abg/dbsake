"""
dbsake.core.mysql.sandbox
~~~~~~~~~~~~~~~~~~~~~~~~~

MySQL sandboxing support

"""
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import os
import time

from dbsake.util import format_filesize
from dbsake.util import path

from . import common
from . import datasource
from . import distribution

info = logging.info
error = logging.error

# expose SandboxError here as a front-end API
SandboxError = common.SandboxError


def create(**options):
    sbopts = common.check_options(**options)

    # a basic sanity check: make sure there's at least 1GB free (or 5%)
    usage = path.disk_usage(sbopts.basedir)

    if usage.free < 1024**3:
        raise SandboxError(("Only {0} of {1} (<{2:.2%}) available on {3}. "
                           "Aborting.").format(
                           format_filesize(usage.free),
                           format_filesize(usage.total),
                           usage.free / usage.total,
                           path.resolve_mountpoint(sbopts.basedir)))

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
    password = common.mkpassword()
    info("    - Generated random password for sandbox user root@localhost")
    common.generate_defaults(sbopts,
                             user='root',
                             password=password,
                             system_user=os.environ['USER'],
                             basedir=dist.basedir,
                             datadir=os.path.join(sbdir, 'data'),
                             socket=os.path.join(sbdir, 'data', 'mysql.sock'),
                             tmpdir=os.path.join(sbdir, 'tmp'),
                             mysql_version=dist.version,
                             port=dist.version.as_int(),
                             innodb_log_file_size=None)
    info("  Bootstrapping sandbox instance")
    common.bootstrap(sbopts, dist, password)
    info("  Creating sandbox.sh initscript")
    common.generate_initscript(sbdir,
                               distribution=dist,
                               datadir=os.path.join(sbdir, 'data'),
                               defaults_file=os.path.join(sbdir,
                                                          'my.sandbox.cnf'))

    info("Sandbox created in %.2f seconds", time.time() - start)
    info("")
    info("Here are some useful sandbox commands:")
    info("       Start sandbox: %s/sandbox.sh start", sbdir)
    info("        Stop sandbox: %s/sandbox.sh stop", sbdir)
    info("  Connect to sandbox: %s/sandbox.sh mysql <options>", sbdir)
    info("   mysqldump sandbox: %s/sandbox.sh mysqldump <options>", sbdir)
    info("Install SysV service: %s/sandbox.sh install-service", sbdir)
