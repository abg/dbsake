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
               shortopts=dict(sandbox_directory="d"))
def mysql_sandbox(sandbox_directory=None):
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
    """

    from . import util
    mysqld_safe = util.which("mysqld_safe")
    mysql = util.which("mysql")
    mysqld_search_path = ['/usr/libexec', '/usr/sbin', os.environ['PATH'] ]
    mysqld = util.which("mysqld", path=os.pathsep.join(mysqld_search_path))

    if not mysqld:
        print("[ERROR] Failed to find mysqld in environment PATH",
              file=sys.stderr)
        return 1

    if not mysqld_safe:
        print("[ERROR] Failed to find mysqld_safe in environment PATH",
              file=sys.stderr)
        return 1

    if not mysql:
        # /usr/bin/mysql missing is not fatal, but probably a serious issue
        print("[WARNING] Failed to find mysql commandline client in path", file=sys.stderr)

    if not sandbox_directory:
        tag = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        sandbox_directory = os.path.expanduser('~/sandboxes/sandbox_' + tag)
    sandbox_directory = os.path.normpath(os.path.abspath(sandbox_directory))

    if os.path.isdir(sandbox_directory) and len(os.listdir(sandbox_directory)):
        print("[ERROR] %s exists and is not empty. Aborting." % sandbox_directory,
              file=sys.stderr)
        return 2

    os.makedirs(sandbox_directory)
    print("Created %s" % sandbox_directory)
    datadir = os.path.join(sandbox_directory, 'data')
    os.makedirs(datadir, 0770)
    print("Created %s" % datadir)
    tmpdir = os.path.join(sandbox_directory, 'tmp')
    os.makedirs(tmpdir, 0770)
    print("Created %s" % tmpdir)

    print("Generating random password for root@localhost...")
    password = util.mkpassword(length=17)

    print("Generating my.sandbox.cnf...")
    defaults = util.generate_defaults(sandbox_directory, user='root', password=password)
    print("Bootstrapping new mysql instance (this may take a few seconds)...")
    print("  Using mysqld=%s" % mysqld)
    bootstrap_log = os.path.join(sandbox_directory, 'bootstrap.log')
    print("  For details see %s" % bootstrap_log)
    try:
        util.bootstrap_mysqld(mysqld=mysqld,
                              defaults_file=defaults,
                              logfile=bootstrap_log,
                              content=util.mysql_install_db(password))
    except IOError:
        print("[ERROR] Bootstrap process failed.  See %s" % bootstrap_log)
        return 1
    print("Bootstrapping complete!")

    initscript = os.path.join(sandbox_directory, 'sandbox.sh')
    print("Generating init script %s..." % initscript)
    util.generate_initscript(sandbox_directory, mysqld_safe=mysqld_safe, mysql=mysql)

    print("Sandbox creation complete!")
    print("You may start your sandbox by running: %s start" % initscript)
    print("You may login to your sandbox by running: %s shell" % initscript)
    print("   or by running: %s --socket=%s" % (mysql, os.path.join(datadir, 'mysql.sock')))
    print("Credentials are stored in %s" % defaults)
    return 0
