Using dbsake
------------

dbsake is a command line tool and has various subcommands.

Running dbsake without any subcommand will show the currently
supports commands.  Each subcommand is documented below.

Here is the basic dbsake usage:

.. code-block:: bash

   Usage: dbsake [options] <command>

   Options:
     -d, --debug
     -q, --quiet
     -V, --version  Show the version and exit.
     -?, --help     Show this message and exit.

   Commands:
     decode         Decode a MySQL tablename as a unicode name.
     encode         Encode a MySQL tablename
     fincore        Report cached pages for a file.
     frmdump        Dump schema from MySQL frm files.
     help           Show help for a command.
     sandbox        Create a sandboxed MySQL instance.
     sieve          Filter a mysqldump plaintext SQL stream
     uncache        Drop OS cached pages for a file.
     upgrade-mycnf  Upgrade a MySQL option file

.. program:: dbsake

.. option:: -?, --help

   Show the top-level dbsake options

.. note::

   Running dbsake <command> --help instead shows the help for that subcommand.

.. option:: -V, --version

   Output the current dbsake version and exit

.. option:: -q, --quiet

   Suppresses all logging output.  Commands that output to stdout will still
   emit output, but no logging will be performed.  You can use the exit
   status of dbsake to detect failure in these cases

.. option:: -d, --debug

   Enable debugging output.  This enables more verbose logs that are typically
   not necessary, but may be helpful for troubleshooting.

sandbox
~~~~~~~

.. versionadded:: 1.0.3

Setup a secondary MySQL instance painlessly.

This setups a MySQL under ~/sandboxes/ (by default) with a
randomly generated password for the root@localhost user
and networking disabled.

A simple shell script is provided to start, stop and connect
to the MySQL instance.

.. versionchanged:: 1.0.5
   dbsake verifies the gpg signature of downloaded MySQL tarball distributions

Usage
.....

.. code-block:: bash

   Usage: dbsake sandbox [OPTIONS]
   
     Create a sandboxed MySQL instance.
   
     This command installs a new MySQL instance under the specified sandbox
     directory, or under ~/sandboxes/sandbox_<datetime> if none is specified.
   
   Options:
     -d, --sandbox-directory <path>  path where sandbox will be installed
     -m, --mysql-distribution <dist>
                                     mysql distribution to install
     -D, --data-source <source>      path to file to populate sandbox
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


.. option:: -D, --data-source <tarball>

   Specify a tarball or directory that will be used for the sandbox datadir.
   If a directory is specified, it will be symlinked to './data' under the
   sandbox directory.  If a tarball is specified it will be extracted to
   the ./data/ path under the sandbox directory, subject to any filtering
   specified by the --table and --exclude-table options.

.. versionadded:: 1.0.4

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
                        

fincore
~~~~~~~

Discover which parts of a file are cached by the OS.

This command uses the mincore() system call on linux to grab a mapping of cached
pages.  Currently this done with a single mincore() call and requires 1-byte for
each 4KiB page.  For very large files, this may require several MiBs or more of
memory.  For a 1TB file this is 256MiB, for instance.

Usage
.....

.. code-block:: bash

   Usage: dbsake fincore [OPTIONS] [PATHS]...
   
     Report cached pages for a file.
   
   Options:
     -v, --verbose
     -?, --help     Show this message and exit.


Example
.......

.. code-block:: bash

   # dbsake fincore /var/lib/mysql/ibdata1
   /var/lib/mysql/ibdata1: total_pages=6656 cached=0 percent=0.00
   # cat /var/lib/mysql/ibdata1 > /dev/null
   # dbsake fincore /var/lib/mysql/ibdata1
   /var/lib/mysql/ibdata1: total_pages=6656 cached=6656 percent=100.00

Options
.......

.. program:: fincore

.. option:: --verbose

   Print each cached page number that is cached.

.. option:: path [path...]

   Path(s) to check for cached pages

uncache
~~~~~~~

Remove a file's contents from the OS cache.

This command is useful when using O_DIRECT.  A file cached by the OS often
causes O_DIRECT to use a slower path - and often buffered + direct I/O is
an unsafe operation anyway.

With MySQL, for instance, a file may be accidentally cached by filesystem
backups that just archive all files under the MySQL datadir.  MySQL itself
may be using innodb-flush-method=O_DIRECT, and once these pages are cached
there can be a performance degradation.  uncache drops these cached pages
from the OS so O_DIRECT can work better.

Usage
.....

.. code-block:: bash

   Usage: dbsake uncache [OPTIONS] [PATHS]...

     Drop OS cached pages for a file.

   Options:
     -?, --help  Show this message and exit.

Example
.......

.. code-block:: bash

   # dbsake fincore /var/lib/mysql/ibdata1
   /var/lib/mysql/ibdata1: total_pages=6656 cached=6656 percent=100.00
   # dbsake uncache /var/lib/mysql/ibdata1
   Uncached /var/lib/mysql/ibdata1
   # dbsake fincore /var/lib/mysql/ibdata1
   /var/lib/mysql/ibdata1: total_pages=6656 cached=0 percent=0.00

Options
.......

.. program:: uncache

.. option:: path [path...]

   Path(s) to remove from cache.

sieve
~~~~~

Filter and transform a mysqldump stream.

This command processes mysqldump output, potentially filtering or
transforming the output based on the provided command line options.

sieve effective works in two modes:

  - streaming; mysqldump is read from ``--input-file`` and written to
    stdout possibly with different output depending on the provided
    options.
  - directory; mysqldump is read from ``--input-file`` and split into
    separate files in the requested directory. This allows converting
    a large dump in a file-per-table easily.  Files output in this
    mode are additionally filtered through ``--compress-command``
    and are processed through ``gzip --fast`` by default so the
    output is compressed on disk by default.


Usage
.....

.. code-block:: bash

   Usage: dbsake sieve [OPTIONS]

     Filter a mysqldump plaintext SQL stream

   Options:
     -F, --format <name>
     -C, --directory <output directory>
     -i, --input-file <path>
     -z, --compress-command <command>
     -t, --table <glob pattern>
     -T, --exclude-table <glob pattern>
     --defer-indexes
     --defer-foreign-keys
     --write-binlog / --disable-binlog
     --table-data / --skip-table-data
     --master-data / --no-master-data
     -f, --force
     -?, --help                      Show this message and exit.

Example
.......

.. code-block:: bash

   $ mysqldump --routines sakila | dbsake sieve --format=directory --directory=backups/
   $ tree backups
   backups
   └── sakila
       ├── actor.sql.gz
       ├── address.sql.gz
       ├── category.sql.gz
       ├── city.sql.gz
       ├── country.sql.gz
       ├── customer.sql.gz
       ├── film_actor.sql.gz
       ├── film_category.sql.gz
       ├── film.sql.gz
       ├── film_text.sql.gz
       ├── inventory.sql.gz
       ├── language.sql.gz
       ├── payment.sql.gz
       ├── rental.sql.gz
       ├── routines.ddl.gz
       ├── staff.sql.gz
       ├── store.sql.gz
       └── views.ddl.gz
   
   1 directory, 18 files

Options
.......

.. program:: sieve

.. versionchanged:: 2.0.0
   Renamed split-mysqldump to sieve; Significant rewrite of functionality.

.. versionchanged:: 2.0.0
   Remove --regex option in favor of -t/--table and -T/--exclude-table option
   which accepts globs.

.. option:: -F, --format <name>

   Output file format.  Must be one of 'stream' or 'directory'. If set to
   'stream', output will be written on stdout.  Unless --force is also
   specified the sieve command with refuse to write to a terminal.

   If set to 'directory', output will be written to the path specified by
   the ``--directory`` option, with a file per table.

.. versionadded:: 2.0.0

.. option:: -C, --directory <output directory>

   Path where the sieve command should create output files. Ignored if
   ``--format`` is set to 'stream'. The sieve command will create this
   path if it does not already exist.

   Defaults to '.' - the current working directory.

.. option:: -i, --input-file <path>

   Input file to read mysqldump input from.  Default to "-" and reads from
   stdin. This must be an uncompressed data source, so to process an already
   compressed .sql.gz file you might run it through
   "zcat backup.sql.gz | dbsake sieve [options...]"

.. versionadded:: 2.0.0

.. option:: -z, --compress-command <command>

   Filter output files through this command. If ``--format`` is not set to
   'directory', then this option is ignored. The sieve command will detect
   most common compression command and create an appropriate extension on the
   output files.  For example, --compress-command=gzip will create .sql.gz
   files under the path specified by ``--directory``.

   Defaults to "gzip -1".

.. versionchanged:: 2.0.0
   -f/--filter-command was renamed to -z/--compress-command

.. option:: -t, --table <glob pattern>

   f ``--table`` is specified, then only tables matching the provided glob
   pattern will be included in the output of the sieve command. Each table
   is qualified by the database name in "database.table" format and then
   compared against the glob pattern. For example, to include all tables
   in the "mysql" database you would specify --table="mysql.*".

   This option may be specified multiple times and sieve will include any
   table that matches at least one of these options so long as the table
   does not also match an ``--exclude-table`` option.

   If no --table options are provided, all tables are included in the output
   that do not otherwise match an ``--exclude-table`` pattern.

.. versionadded:: 2.0.0
 
.. option:: -T, --exclude-table <glob pattern>

   If ``--exclude-table`` is specified, then only tables not matching
   the provided glob pattern will be included in the output of the sieve
   command. Each table is qualified by the database name in "database.table"
   format and then compared against the glob pattern.  For example, to exclude
   the mysql.user table from output you would specify the option:
   "--exclude-table=mysql.user".

   This option may be specified multiple times and sieve will include any
   table that matches at least one of these options so long as the table
   does not also match an ``--exclude-table`` option.

   If no ``--exclude-table`` options are provided, all tables are included in
   the output that match at least one ``--table`` pattern, or all output is
   included if neither ``--exclude-table`` or ``--table`` options are provided.

.. versionadded:: 2.0.0

.. option:: --defer-indexes

   This option rewrites the output of CREATE TABLE statements and arranges for
   secondary indexes to be created after the table data is loaded.  This causes
   an additional ALTER TABLE statement to be output after the table data section
   of each table, when there is at least one secondary index to be added.

   If there are foreign key constraints on the table, associated indexes will
   not be deferred unless the ``--defer-foreign-keys`` option is also specified.

   This option only applies to InnoDB tables and is only efficient on MySQL 5.1+
   (if the innodb plugin is enabled) or on MySQL 5.5+ (default InnoDB engine),
   where the fast alter path may be used.

.. option:: --defer-foreign-keys

   This option rewrites the output of CREATE TABLE statements and adds foreign
   key constraints after the table data is loaded.  This is primarily useful
   to allow deferring secondary indexes with associated foreign keys.

   This option only makes sense if reloading a dump into MySQL 5.6+, othrewise
   adding indexes will require a full table rebuild and will end up being
   much slower than just reloading the mysqldump unaltered.

.. option:: --write-binlog / --disable-binlog

   If ``--disable-binlog`` is set, sieve will output a SET SQL_LOG_BIN=0 SQL
   command to the beginning of the dump to avoid writing to the binary log
   when reloading the resulting output.  Use the option with care, as the
   resulting dump will not replicate to a slave if this option is set.

.. versionadded:: 2.0.0

.. option:: --table-data / --skip-table-data

  If ``--skip-table-data`` is set, sieve will not output any table data
  sections and only output DDL.  Reloading such a dump will result in
  empty tables.

.. versionadded:: 2.0.0

.. option:: --master-data / --no-master-data

   If the ``--master-data`` option is set, any commented out CHANGE MASTER
   statements will be uncommented in the output.  This is useful of setting
   up a replication slave from a backup created using --master-data=2.

   If the ``--no-master-data`` option is set, any CHANGE MASTER statements
   will be commented out in the output, ensuring no CHANGE MASTER is run.
   This is useful for dumps created with --master-data[=1].

.. versionadded:: 2.0.0

.. option:: -f, --force

   The ``--force`` option will force output to be written to stdout even if it
   appears that this will write to an active terminal. This can be useful in
   cases when filtering the mysqldump output or when not outputing large
   amounts of data and want to read it directly on the terminal.
 
upgrade-mycnf
~~~~~~~~~~~~~

Copy a my.cnf file and patch any deprecated options.

This command is used to rewrite a my.cnf file and either strip out or rewrite
options that are not compatible with a newer version of MySQL.

The original my.cnf is left untouched.  A new my.cnf is output on stdout and
reasons for rewriting or excluding options are output on stderr.  

If -p, --patch is specified a unified diff is output on stdout rather than
a full my.cnf.  --patch is required if a my.cnf includes any !include*
directives.

Usage
.....

.. code-block:: bash

   Usage: dbsake upgrade-mycnf [OPTIONS]
   
     Upgrade a MySQL option file
   
   Options:
     -c, --config PATH               my.cnf file to parse
     -t, --target [5.1|5.5|5.6|5.7]  MySQL version to target
     -p, --patch                     Output unified diff rather than full config
     -?, --help                      Show this message and exit.

Example
.......

.. code-block:: bash

   $ dbsake upgrade-mycnf -t 5.6 --patch /etc/my.cnf
   2014-01-04 05:36:34,757 Removing option 'skip-external-locking'. Reason: Default behavior in MySQL 4.1+
   --- a/etc/my.cnf
   +++ b/etc/my.cnf
   @@ -17,7 +17,6 @@
    datadir                         = /var/lib/mysql
    #tmpdir                         = /var/lib/mysqltmp
    socket                          = /var/lib/mysql/mysql.sock
   -skip-external-locking           = 1
    open-files-limit                = 20000
    #sql-mode                       = TRADITIONAL
    #event-scheduler                = 1
    

Options
.......

.. program:: upgrade-mycnf

.. option:: -c <config>, --config <config>

   Specify which my.cnf file to process
   Defaults to /etc/my.cnf

.. option:: -t <version>, --target <version>

   Specify which version of MySQL to target.
   This controls which options are rewritten based on the deprecated options in
   the target MySQL version.
   Defaults to 5.5

.. option:: -p, --patch

   Specify the output should be a unified diff rather than a full my.cnf.
   Defaults to outputting a full my.cnf if this option is not specified.

.. _frmdump:

frmdump
~~~~~~~

Decode a MySQL .frm file and output a CREATE VIEW or CREATE TABLE statement.

This command does not require a MySQL server and interprets a .frm file
according to rules similar to the MySQL server.

For more information on how this command works see :ref:`frm_format`

.. important::
   This program only decodes data strictly available in the .frm file.
   InnoDB foreign-key references are not preserved and AUTO_INCREMENT values
   are also not preserved as these are stored outside of the .frm.

Usage
.....

.. code-block:: bash

   Usage: dbsake frmdump [options] [path[, path...]]
   
     Dump schema from MySQL frm files.
   
   Options:
     -r, --raw-types
     -R, --replace
     -?, --help       Show this message and exit.

Example
.......

.. code-block:: bash


   $ dbsake frmdump /var/lib/mysql/mysql/plugin.frm
   --
   -- Table structure for table `plugin`
   -- Created with MySQL Version 5.6.15
   --
   
   CREATE TABLE `plugin` (
     `name` varchar(64) NOT NULL DEFAULT '',
     `dl` varchar(128) NOT NULL DEFAULT '',
     PRIMARY KEY (`name`)
   ) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT 'MySQL plugins';

   $ dbsake frmdump /var/lib/mysql/sakila/actor_info.frm
   --
   -- View:         actor_info
   -- Timestamp:    2014-01-04 05:29:55
   -- Stored MD5:   402b8673b0c61034644b5b286519d3f1
   -- Computed MD5: 402b8673b0c61034644b5b286519d3f1
   --
   
   CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY INVOKER VIEW `actor_info` select `a`.`actor_id` AS `actor_id`,`a`.`first_name` AS `first_name`,`a`.`last_name` AS `last_name`,group_concat(distinct concat(`c`.`name`,': ',(select group_concat(`f`.`title` order by `f`.`title` ASC separator ', ') from ((`sakila`.`film` `f` join `sakila`.`film_category` `fc` on((`f`.`film_id` = `fc`.`film_id`))) join `sakila`.`film_actor` `fa` on((`f`.`film_id` = `fa`.`film_id`))) where ((`fc`.`category_id` = `c`.`category_id`) and (`fa`.`actor_id` = `a`.`actor_id`)))) order by `c`.`name` ASC separator '; ') AS `film_info` from (((`sakila`.`actor` `a` left join `sakila`.`film_actor` `fa` on((`a`.`actor_id` = `fa`.`actor_id`))) left join `sakila`.`film_category` `fc` on((`fa`.`film_id` = `fc`.`film_id`))) left join `sakila`.`category` `c` on((`fc`.`category_id` = `c`.`category_id`))) group by `a`.`actor_id`,`a`.`first_name`,`a`.`last_name`;

Options
.......

.. program:: frmdump

.. versionchanged:: 2.0.0
   frm-to-schema was renamed to frmdump

.. option:: -R, --replace

   Output view as CREATE OR REPLACE so that running the DDL against MySQL will
   overwrite a view.

.. option:: -r, --raw-types

   Add comment to base tables noting the underlying mysql type code
   as MYSQL_TYPE_<name>.

.. option:: path [path...]

   Specify the .frm files to generate a CREATE TABLE command from.

.. versionadded:: 1.0.2
   Support for indexes with a prefix length in binary .frm files; e.g. KEY (blob_value(255))

.. versionchanged:: 1.0.2
   Views are parsed from .frm files rather than skipped.

.. versionchanged:: 1.0.2
   Raw MySQL types are no longer added as comments unless the --raw-types
   option is specified.

.. versionchanged:: 1.0.2
   A -- Table structure for table \`<name>\` comment is added before each table

.. versionadded:: 1.0.2
   The :option:`frmdump --raw-types` option

.. versionadded:: 1.0.2
   The :option:`frmdump --replace` option

decode
~~~~~~

Decode a MySQL encoded filename

As of MySQL 5.1, tablenames with special characters are encoded with a custom
"filename" encoding.  This command reverses that process to output the original
tablename.

Usage
.....

.. code-block:: bash

   Usage: dbsake decode [options] [NAMES]...

     Decode a MySQL tablename as a unicode name.

   Options:
     -?, --help  Show this message and exit.

Example
.......

.. code-block:: bash

   $ dbsake decode $(basename /var/lib/mysql/test/foo@002ebar.frm .frm)
   foo.bar

Options
.......

.. program:: filename-to-tablename

.. option:: path [path...]

   Specify a filename to convert to plain unicode

encode
~~~~~~

Encode a MySQL tablename with the MySQL filename encoding

This is the opposite of filename-to-tablename, where it takes a normal
tablename and converts it using MySQL's filename encoding.

Usage
.....

.. code-block:: bash

   Usage: dbsake encode [options] [NAMES]...

     Encode a MySQL tablename

   Options:
     -?, --help  Show this message and exit.

Example
.......

.. code-block:: bash

   $ dbsake encode foo.bar
   foo@002ebar

Options
.......

.. program:: encode

.. option:: path [path...]

   Specify a tablename to convert to an encoded filename

