"""
dbsake.sandbox
~~~~~~~~~~~~~~

MySQL temporary instance  support

"""
from __future__ import print_function

import os
import sys
import time

from dbsake import baker


@baker.command(name='mysql-sandbox',
               shortopts=dict(sandbox_directory='d',
                              mysql_source='m'))
def mysql_sandbox(sandbox_directory=None, mysql_source='system'):
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
    """
    from . import util
    from . import distribution

   
    if not sandbox_directory:
        tag = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        sandbox_directory = os.path.expanduser('~/sandboxes/sandbox_' + tag)
    sandbox_directory = os.path.normpath(os.path.abspath(sandbox_directory))

    if os.path.isdir(sandbox_directory) and len(os.listdir(sandbox_directory)):
        print("[ERROR] %s exists and is not empty. Aborting." % sandbox_directory,
              file=sys.stderr)
        return 2

    if util.disk_usage(sandbox_directory).free < 1024**3:
        print("<1GiB free on %s. Aborting." % sandbox_directory)
        return 5

    for name in ('data', 'tmp'):
        path = os.path.join(sandbox_directory, name)
        if util.mkdir_p(path, 0o0770):
            print("Created %s" % path)

    datadir = os.path.join(sandbox_directory, 'data')

    if mysql_source == 'system':
        meta = distribution.distribution_system(sandbox_directory)
    else:
        meta = distribution.distribution_version(sandbox_directory, version=mysql_source)

    print("Generating random password for root@localhost...")
    password = util.mkpassword(length=17)

    print("Generating my.sandbox.cnf...")
    defaults = util.generate_defaults(sandbox_directory, user='root', password=password, metadata=meta)
    print("Bootstrapping new mysql instance (this may take a few seconds)...")
    print("  Using mysqld=%s" % meta.mysqld)
    bootstrap_log = os.path.join(sandbox_directory, 'bootstrap.log')
    print("  For details see %s" % bootstrap_log)
    try:
        util.bootstrap_mysqld(mysqld=meta.mysqld,
                              defaults_file=defaults,
                              logfile=bootstrap_log,
                              content=util.mysql_install_db(password, meta.pkgdatadir))
    except IOError:
        print("[ERROR] Bootstrap process failed.  See %s" % bootstrap_log)
        return 1
    print("Bootstrapping complete!")

    initscript = os.path.join(sandbox_directory, 'sandbox.sh')
    print("Generating init script %s..." % initscript)
    util.generate_initscript(sandbox_directory, mysqld_safe=meta.mysqld_safe, mysql=meta.mysql)

    print("Sandbox creation complete!")
    print("You may start your sandbox by running: %s start" % initscript)
    print("You may login to your sandbox by running: %s shell" % initscript)
    print("   or by running: %s --socket=%s" % (meta.mysql, os.path.join(datadir, 'mysql.sock')))
    print("Credentials are stored in %s" % defaults)
    return 0
