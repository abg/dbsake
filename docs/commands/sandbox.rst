sandbox
-------

.. versionadded:: 1.0.3

Setup a secondary MySQL instance painlessly.

This setups a MySQL under ~/sandboxes/ (by default) with a
randomly generated password for the root@localhost user
and networking disabled.

A simple shell script is provided to start, stop and connect
to the MySQL instance.

.. versionchanged:: 1.0.5
   dbsake verifies the gpg signature of downloaded MySQL tarball distributions

.. important::
   As of dbsake 2.0.0, the sandbox options have changed.  -D is now an alias for
   --datadir, although it was previously an alias for --data-source.  The -s
   option is now an alias for --data-source in order to specify a tarball to
   seed the sandbox instance with.  See :option:`sandbox --datadir` and
   :option:`sandbox --data-source` for more information.

Usage
.....

.. code-block:: bash

   Usage: dbsake.sh sandbox [OPTIONS]
   
     Create a sandboxed MySQL instance.
   
     This command installs a new MySQL instance under the specified sandbox
     directory, or under ~/sandboxes/sandbox_<datetime> if none is specified.
   
   Options:
     -d, --sandbox-directory <path>  path where sandbox will be installed
     -m, --mysql-distribution <dist>
                                     mysql distribution to install
     -D, --datadir <path>            Path to datadir for sandbox
     -s, --data-source <source>      path to file to populate sandbox
     -t, --table <glob-pattern>      db.table glob pattern to include from
                                     --data-source
     -T, --exclude-table <glob-pattern>
                                     db.table glob pattern to exclude from
                                     --data-source
     -c, --cache-policy <policy>     cache policy to apply when downloading mysql
                                     distribution
     --skip-libcheck                 skip check for required system libraries
     --skip-gpgcheck                 skip gpg verification of download mysql
                                     distributions
     --force                         overwrite existing sandbox directory
     -p, --password                  prompt for password to create root@localhost
                                     with
     -x, --innobackupex-options <options>
                                     additional options to run innobackupex
                                     --apply-logs
     -?, --help                      Show this message and exit.


Example
.......

.. code-block:: bash

   # dbsake sandbox --sandbox-directory=/opt/mysql-5.6.19 \
   >                --mysql-distribution=5.6.19 \
   >                --data-source=backup.tar.gz
   Preparing sandbox instance: /opt/mysql-5.6.19
     Creating sandbox directories
       * Created directories in 0.00 seconds
     Preloading sandbox data from /root/backup.tar.gz
   (100.00%)[========================================] 276.0KiB / 276.0KiB
       - Sandbox data appears to be unprepared xtrabackup data
       - Running: /root/xb/bin/innobackupex --apply-log  .
       - (cwd: /opt/mysql-5.6.19/data)
       - innobackupex --apply-log succeeded. datadir is ready.
       * Data extracted in 4.46 seconds
     Deploying MySQL distribution
       - Deploying MySQL 5.6.19 from download
       - Downloading from http://cdn.mysql.com/Downloads/MySQL-5.6/mysql-5.6.19-linux-glibc2.5-x86_64.tar.gz
       - Importing mysql public key to /root/.dbsake/gpg
       - Verifying gpg signature via: /bin/gpg2 --verify /root/.dbsake/cache/mysql-5.6.19-linux-glibc2.5-x86_64.tar.gz.asc -
       - Unpacking tar stream. This may take some time
   (100.00%)[========================================] 291.4MiB / 291.4MiB
       - GPG signature validated
       - Stored MD5 checksum for download: /root/.dbsake/cache/mysql-5.6.19-linux-glibc2.5-x86_64.tar.gz.md5
       * Deployed MySQL distribution in 46.17 seconds
     Generating my.sandbox.cnf
       - Generated random password for sandbox user root@localhost
       ! Existing ib_logfile0 detected. Setting innodb-log-file-size=5M
       ! Found existing shared innodb tablespace: ibdata1:18M:autoextend
       * Generated /opt/mysql-5.6.19/my.sandbox.cnf in 0.03 seconds
     Bootstrapping sandbox instance
       - Logging bootstrap output to /opt/mysql-5.6.19/bootstrap.log
       - User supplied mysql.user table detected.
       - Skipping normal load of system table data
       - Ensuring root@localhost exists
       * Bootstrapped sandbox in 2.04 seconds
     Creating sandbox.sh initscript
       * Generated initscript in 0.01 seconds
   Sandbox created in 52.72 seconds
   
   Here are some useful sandbox commands:
          Start sandbox: /opt/mysql-5.6.19/sandbox.sh start
           Stop sandbox: /opt/mysql-5.6.19/sandbox.sh stop
     Connect to sandbox: /opt/mysql-5.6.19/sandbox.sh mysql <options>
      mysqldump sandbox: /opt/mysql-5.6.19/sandbox.sh mysqldump <options>
   Install SysV service: /opt/mysql-5.6.19/sandbox.sh install-service

Options
.......

.. program:: sandbox

.. versionchanged:: 2.0.0
   mysql-sandbox renamed to sandbox

.. option:: -d, --sandbox-directory <path>

   Specify the path under which to create the sandbox. This defaults
   to ~/sandboxes/sandbox_$(date +%Y%m%d_%H%M%S)

.. versionchanged:: 1.0.6
   --sandbox-directory supports relative paths

.. option:: -m, --mysql-distribution <name>

   Specify the source for the mysql distribution.  This can be one of:

        * system - use the local mysqld binaries already installed on
                     the system
        * mysql*.tar.gz - path to a tarball distribution
        * <mysql-version> - if a mysql version is specified then an
                            attempt is made to download a binary tarball
                            from dev.mysql.com and otherwise is identical
                            to installing from a local tarball

   The default, if no option is specified, will be to use system which
   copies the minimum binaries from system director to $sandbox_directory/bin/.

.. versionchanged:: 1.0.4
   --mysql-source was renamed to --mysql-distribution

.. note::
   --mysql-distribution = <version> will only auto-download tarballs from
   mysql.com.  To install Percona or MariaDB sandboxes, you will need
   to download the tarballs separately and specify the tarball path
   via --mysql-distribution /path/to/my/tarball


.. option:: -D, --datadir <path>

   Specify the path to the datadir to be used for the sandbox.  If this path
   does not exist, it will be created.  The datadir will be boostrapped using
   the MySQL version specified via the :option:`sandbox --mysql-distribution`
   option.  Sanity checks will be done against the path to verify that it
   is either empty or seems to be a valid, unused MySQL datadir.

.. versionadded:: 2.0.0

.. option:: -s, --data-source <tarball>

   Specify a tarball that will be used for the sandbox datadir. If a tarball
   is specified it will be extracted to the ./data/ path under the sandbox
   directory, subject to any filtering specified by the --table and
   --exclude-table options.

.. versionadded:: 1.0.4

.. versionchanged:: 2.0.0
   The ``-s`` short option was added.  In 1.0 this was ``-D``, but as of
   2.0.0, -D is an alias for --datadir.

.. versionchanged:: 2.0.0
   --data-source now only takes a tarball option.  To use an existing datadir,
   use the :option:`sandbox --datadir` option.

.. versionchanged:: 1.0.5
   A directory may be specified for the --data-source option to use an
   existing datadir for the sandbox.

.. note::
   Support for tarballs in --data-source is presently limited to tarballs
   relative to the datadir - such as those generated by percona-xtrabackup or
   certain LVM snapshot backup utilities.

   Directory data sources have no filtering applied even if --table or
   --exclude-table options were provided.

.. option:: -t, --table <glob>

   Specify a glob pattern to filter elements from the --data-source option. If
   --data-source is not specified this option has no effect. <glob> should be
   of the form database.table with optional glob special characters.  This use
   the python fnmatch mechanism under the hood so is limited to only the \*, ?,
   [seq] and [!seq] glob operations.

.. versionadded:: 1.0.4

.. versionchanged:: 2.0.0
   ``--table="mysql.*"`` is included by default in the list of table options
   regardless of other :option:`sandbox --table` optons. Tables in the mysql
   schema can be excluded by using the :option:`sandbox --exclude-table`
   option.

.. option:: -T, --exclude-table <glob>

   Specify a glob pattern to filter elements from the --data-source option.  If
   --data-source is not specified this option has no effect.

.. versionadded:: 1.0.4

.. option:: -c, --cache-policy <always|never|refresh|local>

   Specify the cache policy if installing a MySQL distribution via a download
   (i.e when only a version is specified). This command will cache downloaded
   tarballs by default in the directory specified by $DBSAKE_CACHE environment
   variable, or ~/.dbsake/cache if this is not specified.

   The cache policies have the following semantics:

     * always - check cache and update the cache if a download is required
     * never - never use the cache - this will always result in a download
     * refresh - skip the cache, but update it from a download
     * local - check cache, but fail if a local tarball is not present

.. versionadded:: 1.0.4

.. option:: --skip-libcheck

   As of dbsake 1.0.5, if a version of MySQL >= 5.5.4 is requested for
   download, dbsake checks for libaio on the system.  Without libaio
   mysqld from any recent version of MySQL will fail to start at all.
   This option allows proceeding anyway in case, dbsake is not detecting libaio
   correctly.  Use of this option will often cause the sandbox process to just
   fail later in the process.

.. versionadded:: 1.0.5

.. option:: --skip-gpgcheck

   Disables verification of the gpg signature when downloading MySQL tarball
   distributions.

.. versionadded:: 1.0.5

.. option:: --force

   Forces overwriting the path specified by ``--sandbox-directory`` if
   it already exists

.. versionadded:: 1.0.9

.. option:: -p, --password

   Prompt for the root@localhost password instead of generating a random
   password (the default behavior).  The password will be read from stdin
   if this option is specified and stdin is not a TTY

.. versionadded:: 1.0.9

.. versionchanged:: 2.0.0
   --prompt-password renamed to --password

.. option:: -x, --innobackupex-options <options>

   Add additional options to the "innobackupex --apply-log {extra options} ."
   commandline that the sandbox command uses to prepare a datadir created
   from an xtrabackup tarball image provided via the ``--data-source``
   opton.

.. versionadded:: 1.0.9


Using the sandbox.sh control script
...................................

Usage: ./sandbox.sh <action> [options]

When creating a sandbox, mysql-sandbox generate a simple bash script to control
the sandbox in ./sandbox.sh under the sandbox directory.  This follows the
pattern of a SysV init script and has many standard actions:

- start

  start the sandbox (noop if already started)

  Note: sandbox.sh start passes any additional options directly to the
        mysqld_safe script.  So you can do things like:
        ./sandbox.sh start --init-file=reset_root.sql

- stop

  stop the sandbox (noop if already stopped)

- restart

  stop then start the sandbox

- condrestart

  only restart if sandbox is running

- status
  check if the sandbox is running


Additionally there are several custom actions to make managing the sandbox
easier:

- metadata

  Outputs some basic information about the sandbox environment including
  the version, the my.cnf being used, and various mysql command paths
  that are used by sandbox.sh

- version

  Output a version string for the mysql server process this sandbox was
  initialized with.

- mysql [options]

  connect to the sandbox using the mysql command line client

  You can pass any option you might pass to mysql here.  I.e:
  ./sanbox.sh mysql -e 'SHOW ENGINE INNODB STATUS\G'
  For convenience the action 'use' is an alias for 'mysql'

- mysqldump [options]

  run mysqldump against the sandbox
    
  Example: ./sandbox.sh mysqldump --all-databases | gzip > backup.sql.gz

- upgrade [options]

  run mysql_upgrade against the sandbox

  Example: ./sandbox.sh upgrade --upgrade-system-tables

  This is useful in conjunction with the --data-source option where you
  might load data from a previous MySQL version into a new version for
  testing and want to perform an in-place upgrade of that data.

- install-service

  attempt to install the sandbox.sh under /etc/init.d and add to default
  runlevels.  This is effectively just an alias for:

.. code-block:: bash

   # cp sandbox.sh /etc/init.d/${name}
   # chkconfig --add ${name} && chkconfig ${name} on

   Under ubuntu update-rc.d is used instead of chkconfig.
                      
   install-service accept one argument as the name of the service to install.
   By default this will be called mysql-${version} where $version is the
   current mysqld version being used (e.g. 5.6.15)
