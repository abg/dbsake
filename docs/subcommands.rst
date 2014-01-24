Using dbsake
------------

dbsake is a command line tool and has various subcommands.

Running dbsake without any subcommand will show the currently
supports commands.  Each subcommand is documented below.

Here is the basic dbsake usage:

.. code-block:: bash

   Usage: dbsake [options] [subcommand] [subcommand-options...]
   
   Options:
     -h, --help     show this help message and exit
     -V, --version  show dbsake version and exit
     -q, --quiet    Silence logging output
     -d, --debug    Enable debug messages

.. program:: dbsake

.. option:: -h, --help

   Show the top-level dbsake options

.. note::

   Running dbsake <subcommand> --help instead shows the help for that subcommand.

.. option:: -V, --version

   Output the current dbsake version and exit

.. option:: -q, --quiet

   Suppresses all logging output.  Commands that output to stdout will still
   emit output, but no logging will be performed.  You can use the exit
   status of dbsake to detect failure in these cases

.. option:: -d, --debug

   Enable debugging output.  This enables more verbose logs that are typically
   not necessary, but may be helpful for troubleshooting.

mysql-sandbox
~~~~~~~~~~~~~

.. versionadded:: 1.0.3

Setup a secondary MySQL instance easily.

This setups a MySQL under ~/sandboxes/ (by default) with a
randomly generated password for the root@localhost user
and networking disabled.

A simple shell script is provided to start, stop and connect
to the MySQL instance.

Usage
.....

.. code-block:: bash

   Usage: dbsake mysql-sandbox [<sandbox_directory>] [<mysql_distribution>] [<data_source>] [<table>] [<exclude_table>] [<cache_policy>]
   
   Create a temporary MySQL instance
   
       This command installs a new MySQL instance under the specified sandbox
       directory, or under ~/sandboxes/sandbox_<datetime> if none is specified.
   
   Options:
   
      -d --sandbox-directory   base directory where sandbox will be installed
                               default: ~/sandboxes/sandbox_<datetime>
      -m --mysql-distribution  what mysql distribution to use for the sandbox;
                               system|<major.minor.release>|<tarball>; default:
                               "system"
      -D --data-source         how to populate the sandbox; this defaults to
                               bootstrapping an empty mysql instance similar to
                               running mysql_install_db
      -t --table               glob pattern include from --data; This option
                               should be in database.table format and may be
                               specified multiple times
      -T --exclude-table       glob pattern to exclude from --data; This option
                               should be in database.table format and may be
                               specified multiple times
      -c --cache-policy        the cache policy to use when downloading an mysql
                               distribution. One of: always,never,refresh,local
                               Default: always


Example
.......

.. code-block:: bash

   $ dbsake mysql-sandbox --sandbox-directory=/opt/mysql-5.6.15 \
   >                      --mysql-distribution=5.6.15 \
   >                      --data-source=backup.tar.gz
   Preparing sandbox instance: /opt/mysql-5.6.15
     Creating sandbox directories
       - Created /opt/mysql-5.6.15/data
       - Created /opt/mysql-5.6.15/tmp
       * Prepared sandbox in 0.00 seconds
     Preloading sandbox data from backup.tar.gz
       - Sandbox data appears to be unprepared xtrabackup data
       - Running: /root/xb/bin/innobackupex --apply-log . > innobackupex.log 2>&1
       - (cwd: /opt/mysql-5.6.15/data)
       - innobackupex --apply-log succeeded. datadir is ready.
       * Data extracted in 15.72 seconds
     Deploying MySQL distribution
       - Attempting to deploy distribution for MySQL 5.6.15
       - Downloading from http://cdn.mysql.com/Downloads/MySQL-5.6/mysql-5.6.15-linux-glibc2.5-x86_64.tar.gz
       - Caching download: /root/.dbsake/cache/mysql-5.6.15-linux-glibc2.5-x86_64.tar.gz
       - Unpacking tar stream. This may take some time
       - Stored MD5 checksum for download: /root/.dbsake/cache/mysql-5.6.15-linux-glibc2.5-x86_64.tar.gz.md5
       - Using mysqld (v5.6.15): /opt/mysql-5.6.15/bin/mysqld
       - Using mysqld_safe: /opt/mysql-5.6.15/bin/mysqld_safe
       - Using mysql: /opt/mysql-5.6.15/bin/mysql
       - Using share directory: /opt/mysql-5.6.15/share
       - Using mysqld --basedir: /opt/mysql-5.6.15
       - Using MySQL plugin directory: /opt/mysql-5.6.15/lib/plugin
       * Deployed MySQL distribution to sandbox in 20.79 seconds
     Generating my.sandbox.cnf
       - Generated random password for sandbox user root@localhost
       ! Existing ib_logfile0 detected. Setting innodb-log-file-size=5M
       * Generated /opt/mysql-5.6.15/my.sandbox.cnf in 0.01 seconds
     Bootstrapping sandbox instance
       - Logging bootstrap output to /opt/mysql-5.6.15/bootstrap.log
       - User supplied mysql.user table detected.
       - Skipping normal load of system table data
       - Ensuring root@localhost exists
       - Generated bootstrap SQL
       - Running /opt/mysql-5.6.15/bin/mysqld --defaults-file=/opt/mysql-5.6.15/my.sandbox.cnf --bootstrap
       * Bootstrapped sandbox in 1.98 seconds
     Creating sandbox.sh initscript
       * Generated initscript in 0.00 seconds
   Sandbox created in 38.50 seconds
   
   Here are some useful sandbox commands:
          Start sandbox: /opt/mysql-5.6.15/sandbox.sh start
           Stop sandbox: /opt/mysql-5.6.15/sandbox.sh stop
     Connect to sandbox: /opt/mysql-5.6.15/sandbox.sh mysql <options>
      mysqldump sandbox: /opt/mysql-5.6.15/sandbox.sh mysqldump <options>
   Install SysV service: /opt/mysql-5.6.15/sandbox.sh install-service


Options
.......

.. program:: mysql-sandbox

.. option:: -d, --sandbox-directory <path>

   Specify the path under which to create the sandbox. This defaults
   to ~/sandboxes/sandbox_$(date +%Y%m%d_%H%M%S)

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


.. option:: -D, --data <tarball>

   Specify a tarball that will be extracted to the sandbox datadir prior
   to the bootstrap process.  This can be used to populate the sandbox
   with existing data prior to being brought online.

.. versionadded:: 1.0.4

.. option:: -t, --table <glob>

   Specify a glob pattern to filter elements from the --data option. If --data
   is not specified this option has no effect. <glob> should be of the form
   database.table with optional glob special characters.  This use the python
   fnmatch mechanism under the hood so is limited to only the \*, ?, [seq] and
   [!seq] glob operations.

.. versionadded:: 1.0.4

.. option:: -T, --exclude-table <glob>

   Specify a glob pattern to filter elements from the --data option.  If --data
   is not specified this option has no effect.

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

   Usage: dbsake fincore [<verbose>] [<paths>...]
   
   Check if a file is cached by the OS
   
       Outputs the cached vs. total pages with a percent.
   
   Options:
   
      --verbose  itemize which pages are cached
   
   Variable arguments:
   
      *paths   check if these paths are cached

Example
.......

.. code-block:: bash

   $ dbsake fincore /var/lib/mysql/ibdata1
   /var/lib/mysql/ibdata1: total_pages=37376 cached=0 percent=0.00
   $ cat /var/lib/mysql/ibdata1 > /dev/null
   $ dbsake fincore /var/lib/mysql/ibdata1
   /var/lib/mysql/ibdata1: total_pages=37376 cached=37376 percent=100.00

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

   Usage: dbsake uncache [<paths>...]

   Uncache a file from the OS page cache

   Variable arguments:

      *paths   uncache files for these paths

Example
.......

.. code-block:: bash

   $ dbsake fincore /var/lib/mysql/ibdata1
   /var/lib/mysql/ibdata1: total_pages=37376 cached=37376 percent=100.00
   $ dbsake uncache /var/lib/mysql/ibdata1
   Uncached /var/lib/mysql/ibdata1
   $ dbsake fincore /var/lib/mysql/ibdata1
   /var/lib/mysql/ibdata1: total_pages=37376 cached=0 percent=0.00

Options
.......

.. program:: uncache

.. option:: path [path...]

   Path(s) to remove from cache.

split-mysqldump
~~~~~~~~~~~~~~~

Split mysqldump output into separate parts.

This command splits mysqldump into a .sql file for each table in the original 
dumpfile.   Files are created under a subdirectory which matches the database
name.  An optional filtering command can be specified to compress these files,
and split-mysqldump defaults to filtering through gzip --fast (gzip -1).

Usage
.....

.. code-block:: bash

   Usage: dbsake split-mysqldump [<target>] [<directory>] [<filter_command>] [<regex>]
   
   Split mysqldump output into separate files
   
   Options:
   
      -t --target          MySQL version target (default 5.5)
      -C --directory       Directory to output to (default .)
      -f --filter-command  Command to filter output through(default gzip -1)
      --regex

Example
.......

.. code-block:: bash

   $ mysqldump sakila | dbsake split-mysqldump -C backups/
   2014-01-04 05:34:01,181 Deferring indexes for sakila.actor (backups/sakila/actor.schema.sql)
   2014-01-04 05:34:01,185 Injecting deferred index creation backups/sakila/actor.data.sql
   2014-01-04 05:34:01,194 Not deferring index `idx_fk_city_id` - used by constraint `fk_address_city`
   2014-01-04 05:34:01,211 Not deferring index `idx_fk_country_id` - used by constraint `fk_city_country`
   2014-01-04 05:34:01,227 Not deferring index `idx_fk_address_id` - used by constraint `fk_customer_address`
   2014-01-04 05:34:01,227 Not deferring index `idx_fk_store_id` - used by constraint `fk_customer_store`
   2014-01-04 05:34:01,227 Deferring indexes for sakila.customer (backups/sakila/customer.schema.sql)
   2014-01-04 05:34:01,231 Injecting deferred index creation backups/sakila/customer.data.sql
   2014-01-04 05:34:01,240 Not deferring index `idx_fk_original_language_id` - used by constraint `fk_film_language_original`
   2014-01-04 05:34:01,240 Not deferring index `idx_fk_language_id` - used by constraint `fk_film_language`
   2014-01-04 05:34:01,240 Deferring indexes for sakila.film (backups/sakila/film.schema.sql)
   2014-01-04 05:34:01,245 Injecting deferred index creation backups/sakila/film.data.sql
   2014-01-04 05:34:01,258 Not deferring index `idx_fk_film_id` - used by constraint `fk_film_actor_film`
   2014-01-04 05:34:01,275 Not deferring index `fk_film_category_category` - used by constraint `fk_film_category_category`
   2014-01-04 05:34:01,300 Not deferring index `idx_fk_film_id` - used by constraint `fk_inventory_film`
   2014-01-04 05:34:01,301 Not deferring index `idx_store_id_film_id` - used by constraint `fk_inventory_store`
   2014-01-04 05:34:01,330 Not deferring index `idx_fk_customer_id` - used by constraint `fk_payment_customer`
   2014-01-04 05:34:01,331 Not deferring index `idx_fk_staff_id` - used by constraint `fk_payment_staff`
   2014-01-04 05:34:01,331 Not deferring index `fk_payment_rental` - used by constraint `fk_payment_rental`
   2014-01-04 05:34:01,380 Not deferring index `idx_fk_staff_id` - used by constraint `fk_rental_staff`
   2014-01-04 05:34:01,380 Not deferring index `idx_fk_customer_id` - used by constraint `fk_rental_customer`
   2014-01-04 05:34:01,381 Not deferring index `idx_fk_inventory_id` - used by constraint `fk_rental_inventory`
   2014-01-04 05:34:01,445 Not deferring index `idx_fk_address_id` - used by constraint `fk_staff_address`
   2014-01-04 05:34:01,446 Not deferring index `idx_fk_store_id` - used by constraint `fk_staff_store`
   2014-01-04 05:34:01,460 Not deferring index `idx_fk_address_id` - used by constraint `fk_store_address`
   2014-01-04 05:34:01,493 Split input into 1 database(s) 16 table(s) and 14 view(s)

Options
.......

.. program:: split-mysqldump

.. option:: -t <version>, --target <version>

   Which version of MySQL the output files should be targetted to.
   This option toggles whether split-mysqldump defers index creation
   until after the data is loaded (5.5+) or whether to defer foreign-key
   creation (5.6+).

   Valid values: 5.1, 5.5, 5.6

.. option:: -C <path>, --directory <path>

   Where split-mysqldump should create output files.
   split-mysqldump will create this path if it does not already exist.
   Defaults to '.' - the current working directory.

.. option:: -f <command>, --filter-command <command>

   Filter output files through this command.
   split-mysqldump will detect most compression commands
   and set an appropriate extension on its output files. E.g.
   -f gzip results in a gz extension, -f "bzip -9" results in
   bz2 extension, etc.

   Defaults to "gzip -1"

.. option:: --regex <pattern>

   Matches tables and views against the provided regex.
   Any object that doesn't match the regex is skipped.
   Defaults to matching all objects.

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

   Usage: dbsake upgrade-mycnf [<config>] [<target>] [<patch>]
   
   Patch a my.cnf to a new MySQL version
   
   Options:
   
      -c --config  my.cnf file to parse (default: /etc/my.cnf)
      -t --target  MySQL version to target the option file (default: 5.5)
      -p --patch   Output unified diff rather than full config (default off)

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

.. _frm-to-schema:

frm-to-schema
~~~~~~~~~~~~~

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

   Usage: dbsake frm-to-schema [<raw_types>] [<replace>] [<paths>...]
   
   Decode a binary MySQl .frm file to DDL
   
   Options:
   
      --raw-types
      --replace    If a path references a view output CREATE OR REPLACE so a view
                   definition can be replaced.
   
   Variable arguments:
   
      *paths   paths to extract schema from

Example
.......

.. code-block:: bash


   $ dbsake frm-to-schema /var/lib/mysql/mysql/plugin.frm
   --
   -- Table structure for table `plugin`
   -- Created with MySQL Version 5.6.15
   --
   
   CREATE TABLE `plugin` (
     `name` varchar(64) NOT NULL DEFAULT '',
     `dl` varchar(128) NOT NULL DEFAULT '',
     PRIMARY KEY (`name`)
   ) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT 'MySQL plugins';

   $ dbsake frm-to-schema /var/lib/mysql/sakila/actor_info.frm
   --
   -- View:         actor_info
   -- Timestamp:    2014-01-04 05:29:55
   -- Stored MD5:   402b8673b0c61034644b5b286519d3f1
   -- Computed MD5: 402b8673b0c61034644b5b286519d3f1
   --
   
   CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY INVOKER VIEW `actor_info` select `a`.`actor_id` AS `actor_id`,`a`.`first_name` AS `first_name`,`a`.`last_name` AS `last_name`,group_concat(distinct concat(`c`.`name`,': ',(select group_concat(`f`.`title` order by `f`.`title` ASC separator ', ') from ((`sakila`.`film` `f` join `sakila`.`film_category` `fc` on((`f`.`film_id` = `fc`.`film_id`))) join `sakila`.`film_actor` `fa` on((`f`.`film_id` = `fa`.`film_id`))) where ((`fc`.`category_id` = `c`.`category_id`) and (`fa`.`actor_id` = `a`.`actor_id`)))) order by `c`.`name` ASC separator '; ') AS `film_info` from (((`sakila`.`actor` `a` left join `sakila`.`film_actor` `fa` on((`a`.`actor_id` = `fa`.`actor_id`))) left join `sakila`.`film_category` `fc` on((`fa`.`film_id` = `fc`.`film_id`))) left join `sakila`.`category` `c` on((`fc`.`category_id` = `c`.`category_id`))) group by `a`.`actor_id`,`a`.`first_name`,`a`.`last_name`;

Options
.......

.. program:: frm-to-schema

.. option:: --replace

   Output view as CREATE OR REPLACE so that running the DDL against MySQL will
   overwrite a view.

.. option:: --raw-types

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
   The :option:`frm-to-schema --raw-types` option

.. versionadded:: 1.0.2
   The :option:`frm-to-schema --replace` option

filename-to-tablename
~~~~~~~~~~~~~~~~~~~~~

Decode a MySQL encoded filename

As of MySQL 5.1, tablenames with special characters are encoded with a custom
"filename" encoding.  This command reverses that process to output the original
tablename.

Usage
.....

.. code-block:: bash

   Usage: dbsake filename-to-tablename [<names>...]
   
   Decode a MySQL tablename as a unicode name
   
   Variable arguments:
   
      *names   filenames to decode


Example
.......

.. code-block:: bash

   $ dbsake filename-to-tablename $(basename /var/lib/mysql/test/foo@002ebar.frm .frm)
   foo.bar

Options
.......

.. program:: filename-to-tablename

.. option:: path [path...]

   Specify a filename to convert to plain unicode

tablename-to-filename
~~~~~~~~~~~~~~~~~~~~~

Encode a MySQL tablename with the MySQL filename encoding

This is the opposite of filename-to-tablename, where it takes a normal
tablename and converts it using MySQL's filename encoding.

Usage
.....

.. code-block:: bash

   Usage: dbsake tablename-to-filename [<names>...]
   
   Encode a unicode tablename as a MySQL filename
   
   Variable arguments:
   
      *names   names to encode


Example
.......

.. code-block:: bash

   $ dbsake tablename-to-filename foo.bar
   foo@002ebar

Options
.......

.. program:: tablename-to-filename

.. option:: path [path...]

   Specify a tablename to convert to an encoded filename

import-frm
~~~~~~~~~~

Takes a source binary .frm and converts it to a MyISAM .frm

.. danger::
   This command is experimental.  The resulting .frm may crash the MySQL server
   in some cases, particularly if converting very old .frms.

This command is intended to essentially import a binary .frm to maintain its
original column definitions which might be lost with a normal CREATE TABLE, or
in cases where the .frm is otherwise not readable by MySQL with its current
storage engine.

This is essentially equivalent to running the MySQL DDL command:

CREATE TABLE mytable LIKE source_table;
ALTER TABLE mytable ENGINE = MYISAM, REMOVE PARTITIONING;

Options
.......

.. program:: import-frm

.. option:: source destination

   import an existing .frm as a MyISAM table to the path specified by destination

read-ib-binlog
~~~~~~~~~~~~~~

Read the binary log coordinates from an innodb shared tablespace

If binary logging is enabled, InnoDB transactionally records the binary log
coordinates relative to InnoDB transactions.  This is stored in the system
header page of the first InnoDB shared tablespace (e.g. /var/lib/mysql/ibdata1
with a standard MySQL configuration).  This command reads the filename and
position of the log coordinates and outputs a friendly CHANGE MASTER command.

Usage
.....

.. code-block:: bash

   Usage: dbsake read-ib-binlog <path>
   
   Extract binary log filename/position from ibdata
   
   Required Arguments:
   
     path
   
Example
.......

.. code-block:: bash

   $ dbsake read-ib-binlog /var/lib/mysql/ibdata1
   CHANGE MASTER TO MASTER_LOG_FILE='mysqld-bin.000003', MASTER_LOG_POS=644905653;

Options
.......

.. program:: read-ib-binlog

.. option:: path

   Specify the path to a shared InnoDB tablespace (e.g. /var/lib/mysql/ibdata1)
   Binary log information will be read from this file.

