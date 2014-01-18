"""
dbsake.mysql.sandbox
~~~~~~~~~~~~~~~~~~~~

MySQL temporary instance  support

"""
from __future__ import print_function

import logging
import os
import sys
import time

from dbsake import baker
from dbsake.util import path

debug = logging.debug
info = logging.info
error = logging.info
fatal = logging.fatal

@baker.command(name='mysql-sandbox',
               multiopts=['table'],
               shortopts=dict(sandbox_directory='d',
                              table='t',
                              data='D',
                              mysql_source='m'))
def mysql_sandbox(sandbox_directory=None,
                  mysql_source='system',
                  data=None,
                  table=()):
    """Create a temporary MySQL instance

    This command installs a new MySQL instance under the
    specified sandbox directory, or under
    ~/sandboxes/sandbox_<datetime> if none is specified.

    The datadir is under ./data/ relative to the sandbox
    directory.  This is configured by the option file in
    ./my.sandbox.cnf.  The instance is controlled by an
    init-script installed under ./sandbox.sh.

    The new instance is not automatically started and
    needs to be started via the sandbox.sh initscript.

        $ ./sandbox.sh start

    The sandbox.sh init-script has an additional command,
    'shell' that can be used to connect directly to the
    sandbox:

        $ ./sandbox.sh shell -e 'select @@datadir'

    The init-script should be suitable to adding as a sysv
    service:

        $ ln -s $PWD/sandbox.sh /etc/init.d/my-mysql-instance

        $ chkconfig --add my-mysql-instance

        $ /etc/init.d/my-mysql-instance start

    :param sandbox_directory: install sandbox under this path
    :param mysql_source: how to find the mysql distribution.
                         may be either 'system' or a mysql version string
                         If a version string, this command will attempt to
                         download a binary tarball from cdn.mysql.com.
    :param data: data source for the new sandbox
                 If not specified, a new mysql instance is bootstrapped
                 similar to running mysql_install_db
    :param table: optional table pattern to extract from data
                  Has no effect if data is not specified
    """
    from . import distribution
    from . import tarball
    from . import util

    if not sandbox_directory:
        tag = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        sandbox_directory = os.path.expanduser('~/sandboxes/sandbox_' + tag)
    sandbox_directory = os.path.normpath(os.path.abspath(sandbox_directory))

    if os.path.isdir(sandbox_directory) and len(os.listdir(sandbox_directory)):
        fatal("%s exists and is not empty. Aborting.", sandbox_directory)
        return 2

    if path.disk_usage(sandbox_directory).free < 1024**3:
        fatal("<1GiB free on %s. Aborting.", sandbox_directory)
        return 5

    for name in ('data', 'tmp'):
        dirpath = os.path.join(sandbox_directory, name)
        if path.makedirs(dirpath, 0o0770, exist_ok=True):
            info("Created %s", dirpath)

    datadir = os.path.join(sandbox_directory, 'data')

    if mysql_source == 'system':
        meta = distribution.distribution_system(sandbox_directory)
    elif os.path.exists(mysql_source) and mysql_source.endswith('.tar.gz'):
        meta = distribution.distribution_tarball(sandbox_directory, mysql_source)
    else: # expect a version number
        meta = distribution.distribution_version(sandbox_directory, version=mysql_source)

    innodb_log_file_size = None
    if data:
        tarball.unpack_datadir(datadir, data, table)
        ib_logfile0 = os.path.join(datadir, 'ib_logfile0')
        try:
            innodb_log_file_size = os.stat(ib_logfile0).st_size
        except OSError:
            debug("No ib_logfile0", excinfo=True)
        # XXX: if there is no ib_logfile0 then this may be unapplied xtrabackup
        #      data - at which point we must apply logs


    # XXX: Resetting a password may be incorrect if data
    #      was specified - it may make sense to register
    #      a separate user
    info("Generating random password for root@localhost...")
    password = util.mkpassword(length=17)

    info("Generating my.sandbox.cnf...")
    defaults = util.generate_defaults(sandbox_directory,
                                      user='root',
                                      password=password,
                                      innodb_log_file_size=innodb_log_file_size,
                                      metadata=meta)
    info("Bootstrapping new mysql instance (this may take a few seconds)...")
    info("  Using mysqld=%s", meta.mysqld)
    bootstrap_log = os.path.join(sandbox_directory, 'bootstrap.log')
    info("  For details see %s", bootstrap_log)
    try:
        util.bootstrap_mysqld(mysqld=meta.mysqld,
                              defaults_file=defaults,
                              logfile=bootstrap_log,
                              content=util.mysql_install_db(password, meta.pkgdatadir))
    except IOError:
        fatal("Bootstrap process failed.  See %s", bootstrap_log)
        return 1
    info("Bootstrapping complete!")

    initscript = os.path.join(sandbox_directory, 'sandbox.sh')
    info("Generating init script %s...", initscript)
    util.generate_initscript(sandbox_directory,
                             mysqld_safe=meta.mysqld_safe,
                             mysql=meta.mysql)

    info("Sandbox creation complete!")
    info("You may start your sandbox by running: %s start", initscript)
    info("You may login to your sandbox by running: %s shell", initscript)
    info("   or by running: mysql --defaults-file=%s", defaults)
    info("Sandbox datadir is located %s", datadir)
    info("Credentials are stored in %s", defaults)
    return 0
