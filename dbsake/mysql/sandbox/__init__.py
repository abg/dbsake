"""
dbsake.mysql.sandbox
~~~~~~~~~~~~~~~~~~~~

MySQL sandboxing support

"""
from __future__ import print_function

import logging
import os
import time

from dbsake import baker

info = logging.info
error = logging.error

@baker.command(name='mysql-sandbox',
               shortopts={ 'sandbox_directory'  : 'd',
                           'mysql_distribution' : 'm',
                           'data_source'        : 'D',
                           'table'              : 't',
                           'exclude_table'      : 'T',
                           'cache_policy'       : 'c'},
               multiopts=['table', 'exclude_table'])
def mysql_sandbox(sandbox_directory=None,
                  mysql_distribution='system',
                  data_source=None,
                  table=(),
                  exclude_table=(),
                  cache_policy='always'):
    """
    Useful docstring here

    :param sandbox_directory: base directory where sandbox will be installed
    :param mysql_distribution: what mysql distribution to use for the sandbox;
                               This defaults to 'system' and this command will
                               attempt to use the currently installed mysql
                               distribution on the system.
    :param data_source: how to populate the sandbox; this defaults to
                        bootstrapping an empty mysql instance with a randomly
                        generated password for the root@localhost user.
    :param table: table to include from the data source
    :param exclude_table: table to exclude from data source;
    :param cache_policy: the cache policy to use when downloading an mysql
                         distribution
    """
    from . import common
    from . import datasource
    from . import distribution

    start = time.time()
    sbopts = common.check_options(**locals())
    try:
        create_sandbox(sbopts)
    except common.SandboxError as exc:
        error("!! Sandbox creation failed: %s", exc)
        return 1
    else:
        return 0

def create_sandbox(sbopts):
    from . import common
    from . import datasource
    from . import distribution
    info("Preparing sandbox instance: %s", sbopts.basedir)
    info("  Creating sandbox directories")
    common.prepare_sandbox_paths(sbopts)
    # Note here that loading from mysqldump sources cannot be done
    # until after the sandbox is bootstrapped
    # And generating defaults cannot be done until we have an innodb-log-file-size
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
                             datadir=os.path.join(sbopts.basedir, 'data'),
                             socket=os.path.join(sbopts.basedir, 'data', 'mysql.sock'),
                             tmpdir=os.path.join(sbopts.basedir, 'tmp'),
                             mysql_version=dist.version,
                             innodb_log_file_size=None,
                            )
    info("  Bootstrapping sandbox instance")
    common.bootstrap(sbopts, dist, password)
    info("  Creating sandbox.sh initscript")
    common.generate_initscript(sbopts.basedir,
                               distribution=dist,
                               datadir=os.path.join(sbopts.basedir, 'data'),
                               defaults_file=os.path.join(sbopts.basedir, 'my.sandbox.cnf'))

    info("Sandbox created in %.2f seconds", time.time() - start)
    info("Here are some useful sandbox commands")

    info("       Start sandbox: %s/sandbox.sh start", sbopts.basedir)
    info("        Stop sandbox: %s/sandbox.sh stop", sbopts.basedir)
    info("  Connect to sandbox: %s/sandbox.sh mysql <options>", sbopts.basedir)
    info("   mysqldump sandbox: %s/sandbox.sh mysqldump <options>", sbopts.basedir)
    info("Install SysV service: %s/sandbox.sh install-service", sbopts.basedir)
    return 0
