.. :changelog:

History
=======

2.1.0 (2015-01-28)
------------------

New features
    * unpack command added to help extracting files from .tar or .xb archives
      See http://docs.dbsake.net/en/latest/commands/unpack.html for for details.

    * "make dbsake.sh" would fail under python2.6 due to some assumptions
      around python's zipfile module.

    * "make test-all" will now test against python2.6, python3.4 environments,
      if available.

Bugs fixed:

  * fincore: handle io errors more gracefully (issue #72)

  * frmdump: decoding/encoding _filename encoding MySQL names is now
             compatible with python3.  This would previously fail under
             python3 in some circumstances.

  * sandbox: sandbox.sh no longer uses the sed -r flag when processing my.cnf
             options to make the script more compatible on non-GNU platforms.
             (issue #70)

  * sandbox: gpg stderr output was previously logged incorrectly
             (issue #74)

  * sandbox: mysqld --init-file is now used to generate the database user
             rather than parsing the user.frm or injecting SQL into the
             bootstrap process.  This resolves an issue with recent MySQL
             5.7 releases and should generally be more robust.

  * sandbox: "sandbox.sh mysql" now sets MYSQL_HISTFILE to .mysql_history
             relative to the sandbox base directory, rather than appending
             to ~/.mysql_history.  This avoids problems mixing libedit w/
             libreadline (issue #76)

  * sandbox: stale pidfiles are now detected and handled gracefully.
             Previously a stale pidfile would require manual intervention
             to remove the mysql.pid or ./sandbox.sh start would fail
             to automatically restart a crashed instance. (issue #75)

  * sandbox: The --datasource option now correctly display progress
             when unpacking a compressed datasource. (issue #73)

  * sandbox: The --datasource option now handles xbstream archives in
             addition to .tar archives and supports more compression
             options for both (.gz, .bz2, .xz and .lzo)

  * sandbox: --progress / --no-progress options have been added to
             control the display of progressbars

  * sandbox: logging more consistently uses whitespace when subtasks
             are completed during sandbox creation.

  * sandbox: The generated my.sandbox.cnf now generates a somewhat
             cleanear default config.  wait-timeout / interactive-timeout
             now use the MySQL defaults rather than being 600 / 3600
             (respectively). The buggy relay-log-space-limit is avoided
             and innodb-buffer-pool-{dump,restore} options are set by
             default on MySQL 5.6+.

  * sandbox: Extracting --datasource archives are now handled via the
             internal unpack command for consistency.

  * sieve: Decompressing compressed input would fail on platforms where
           flushing read-only files results in an EBADF file.  (Issue #71)

  * sieve: documentation incorrectly referenced "--no-write-binlog" as
           "--disable-binlog" (issue #81)

  * sieve: mariadb gtid information in mysqldump output is now handled
           properly (issue #78)

  * upgrade-mycnf: The example in the documentation was incorrectly missing
                   the -c / --config option. (issue #82)


2.0.0 (2014-08-05)
------------------

The 2.0.0 release is a major update to dbsake significantly updating
various internals and introducing some backwards incompatible changes.

As of 2.0.0, dbsake uses `semantic versioning <http://semver.org/>`_ and new
features will only be introduced in point releases (2.1, 2.2, 2.3, etc.) Only
strict bug fixes will be introduced in patch releases (2.0.1, 2.0.2, etc.)
going forward.  Incompatible changes will only be introduced in major version
bumps (3.0, 4.0, etc.).

Compatibility changes:

  * frm-to-schema command has been renamed to frmdump
  * frmdump -r/--raw-types option was renamed to -t/--type-codes
  * mysql-sandbox command has been renamed to sandbox
  * filename-to-tablename command has been renamed to decode-tablename
  * tablename-to-filename command has been renamed to encode-tablename
  * importfrm command has been removed
  * read-ibbinlog command has been removed
  * split-mysqldump has been completely redesigned and renamed to "sieve",
    with many more capabilities than the old split-mysqldump command. Read the
    `sieve documentation <http://docs.dbsake.net/en/latest/commands/sieve.html>`_
    for more information.
  * dbsake 2.0+ uses `click <http://click.pocoo.org/>`_ for option parsing
    instead of `baker.py <https://pypi.python.org/pypi/Baker/1.3>`_ used
    in 1.0. This provides a more standard option parsing experience, but
    this means dbake no longer accepts position arguments interchangably
    with options.
  * The sandbox command now uses jinja2 to generate templates rather than
    tempita.
  * sandbox -D is now a short option for --datadir.  Use -s as a short
    option for --data-source.
  * sandbox --prompt-password was shortened to simply --password
  * dbsake no longer uses the sarge library internally
  * dbsake no longer uses the tempita library internally

New features:

  * dbsake now supports bash completion via click. See
    `Enable bash completion <http://docs.dbsake.net/en/latest/cli.html#enabling-bash-completion>`_
    for details.
  * sandbox now uses system compression commands to decompress tarballs
    from the --data-source option rather than strictly relying on the
    python standard library.  This should speed up creating a sandbox
    from existing data in some cases and supports more compression
    formats (.gz,.bz2, .lzo, .xz)  (Issue #64)
  * sandbox now includes the mysql.* schema by default when performing
    partial restores from existing data (e.g. -D backup.tar.gz -t mydb.*).
    Restoring mysql tables to the sandbox can be suppressed with the
    -T / --exclude-table 'mysql.*' option. (Issue #67)
  * sandbox now generates a simplified sandbox.sh shell script file.
    The sandbox.sh script now read mysql server options from the my.sandbox.cnf
    config file rather than hardcoding various options in sandbox.sh. This
    would previously make it tedious to change the path for log-error or
    other options.
  * sandbox no longer generates a sandbox.sh which sources /etc/sysconfig.
  * sandbox now supports a -u/--mysql-user option for specifying the
    database user created during sandbox setup.
  * sandbox now supports a -D / --datadir option for specifying the MySQL
    datadir that should be used for a sandbox.  This supersedes support for
    --data-source=<directory>, which now only supports tarball targets.
  * frmdump now handles MariaDB microsecond precision date/time types.
  * fincore and uncache no longer fail when no paths are passed.  This usage
    is now considered a no-op.

Bugs fixed:

  * sandbox failed to create ./tmp/ when overwriting an existing sandbox
    directory with --force, if ./data/ already existed but ./tmp did not.
    (Issue #65)
  * sandbox now handles 5.0 / 5.1 binary tarball installs more robustly.
    Previously, mysqld_safe would fail to find my_print_defaults in the
    sandbox directory and could fail if sandbox.sh was run when
    the current working directory != sandbox directory. (Issue #66)
  * frmdump incorrectly defaulted to SQL SECURITY INVOKER when decoding view
    .frm files.  This behavior has been changed to use MySQL's default of
    SQL SECURITY DEFINER.
  * frmdump did not match MySQL output when decoding views
  * frmdump did not correctly decode default values for 3-byte MEDIUM int
    fields due to several logic errors.
  * frmdump did not include the unsigned attribute for float / double fields
    which were defined with a (precision, scale) scale attribute.
  * frmdump did not format MariaDB TIME fields with microsecond precision
    correctly.
  * frmdump did not format MariaDB TIMESTAMP fields with microsecond precision
    correctly.
  * frmdump did not format MariaDB DATETIME(N) with microsecond precision
    correctly.
  * frmdump did not handle timestamp values that defaulted to '0' correctly,
    and instead used '1970-01-01 00:00:00' as the default, rather than the
    MySQL convention of using '0000-00-00 00:00:00'
  * frmdump did not always format microseconds for MySQL 5.6 DATETIME(N)
    fields correctly.

1.0.9 (2014-07-09)
------------------

New features:

 * mysql-sandbox now provides a --force option to disable various
   sanity checks allowing installing into an existing directory
   (issue #47)
 * mysql-sandbox now provides a --prompt-password option for setting the
   root@localhost password for a new sandbox. This is a boolean option
   that will either prompt for a password (if stdin is attached to a TTY)
   or read the password directly from stdin. (issue #53)
 * mysql-sandbox now generates my.sandbox.cnf with relay-log and bin-log
   options relative to the datadir.  These options are still commented out
   by default, but now do not reference the non-standard /var/lib/mysqllogs
   path. (issue #51)
 * mysql-sandbox now includes a commented out "#port = <version>" option
   in the generated my.sandbox.cnf options file. (issue #55)
 * mysql-sandbo now provides a --innobackupex-options/-x option to allow
   passing arbitrary options to innobackupex --apply-log when bootstrapping
   a sandbox from an xtrabackup tarball backup image (issue #56)

Bugs fixed:

 * mysql-sandbox now includes a comment indiciating the version of dbsake
   in both the generated sandbox.sh and my.sandbox.cnf files (issue #42)
 * mysql-sandbox now reports errors better when a binary tarball cannot
   be found on the MySQL CDN (issue #44)
 * mysql-sandbox now provides more details when encountering a bad
   mysql tarball distribution (issue #46)
 * mysql-sandbox no longer raises an unchecked exception when --data-source
   specifies a datadir without an ib_logfile (issue #49)
 * mysql-sandbox now bootstraps sandboxes with default-storage-engine=MyISAM
   in order to handle TokuDB binary tarball distributions better (issue #50)
 * mysql-sandbox now sets the no-auto-rehash option for the mysql client
   in my.sandboc.cnf's [mysql] section.
 * mysql-sandbox now only sets the mysql.user plugin field to
   'mysql_native_password' for MySQL 5.7. This otherwise causes issues
   for MariaDB when bootstrapping MariaDB from MySQL 5.6+ data. (issue #54)
 * frm-to-schema no longer fails when using the --raw-types option. This
   was broken in v1.0.8 as part of a fix for issue #38. (issue #45)

1.0.8 (2014-04-02)
------------------

Bug fixes:

 * mysql-sandbox now fails more gracefully if bootstrap files are invalid or
   not found in a MySQL distribution (issue #37)
 * mysql-sandbox now correctly uses /usr/share/percona-server rather than
   trying to use a missing or incorrect /usr/share/mysql for system installs
   of Percona Server (issue #41)
 * mysql-sandbox is now less chatty and many less critical details are only
   logged with dbsake --debug to reduce spam
 * frm-to-schema now correctly decodes default values for old MySQL varchar
   columns generated by servers prior to MySQL 5.0. (issue #36)
 * frm-to-schema now decodes unicode metadata identifiers correctly rather than
   failing on a parsing error (issue #38)
 * frm-to-schema now formats TEXT types (tinytext, mediumtext, text, longtext)
   with the associated column level charset or collation (issue #40)
 * split-mysqldump nows correctly handles dump files generated with mysqldump
   --flush-privileges (issue #33)
 * split-mysqldump now handles a commented CHANGE MASTER line generated by
   mysqldump --master-data=2 (issue #33)


1.0.7 (2014-02-20)
------------------

Bug fixes:

 * dbsake frm-to-schema now reads signed MEDIUMINT default values; Previously a
   bug caused an uncaught exception to be thrown (issue #19)
 * dbsake frm-to-schema now interprets negative signed MEDIUMINT default values
   correctly; Previously this would result in incorrect values (issue #23)
 * dbsake frm-to-schema introduced a bug in v1.0.6 that caused an exception
   when formatting BIGINT default values (issue #20)
 * dbsake frm-to-schema should now handle nullable columns more robustly; This
   addresses the improper fix made in v1.0.6 for issue #9. Previously this
   command was not honoring all the table handler options resulting in
   spuriously misinterpretting a column's default value as NULL. (issue #21)
 * dbsake frm-to-schema has improved the formatting for float/double column's
   default values; Previously this used default python precision in output
   which was often inaccurate for 'float' and generally did not match the
   output from mysql SHOW CREATE TABLE (issue #22)
 * dbsake frm-to-schema now display table comments similar to SHOW CREATE TABLE
   Previously this was displayed with a space separator as "COMMENT '<value>'"
   but now is display as "COMMENT='<value>'" (issue #24)
 * dbsake frm-to-schema now displays decimal default values correctly in cases
   where the encoded decimal bytes were not a multiple of 4 (issue #26)
 * dbsake frm-to-schema now trims insignificant zeros from the interger part
   of a decimal value; Previously this would display decimal(19, 0) default '0'
   as default '000' due to implementation details of the decoding algorithm
   (issue #27)

 * dbsake mysql-sandbox now checks for the existence of mysql installation .sql
   scripts; Previously this woudl result in an uncaught exception if
   /usr/share/mysql existed but the files necessary for bootstrapping did
   not (issue #25)
 * dbsake mysql-sandbox now creates the performance_schema database and
   tables under MariaDB 5.5+ (issue #28)


1.0.6 (2014-02-17)
------------------

New features:

 * dbsake mysql-sandbox's generated ./sandbox.sh start/stop actions now show
   progress more visibly by echoing a '.' once a second until the start/stop
   action finishes (issue #18)

Bugs fixed:

 * dbsake now parses boolean options correctly; previously these would
   sometimes consume the next argument in the commandline (issue #8)

 * dbsake split-mysqldump now supports deferring indexes specified with an
   algorithm; previously these weren't matched correctly and thus would
   never be deferred.
 * dbsake split-mysqldump now aborts if an invalid mysqldump header is
   detected.  previously it was queing lines looking for the end of the
   header and used excessive memory and ultimately failing (issue #17)

 * dbsake frm-to-schema now handles null values for blob types (issue #9)
 * dbsake frm-to-schema now quotes integer default values; Previously
   a default of 0 was unquoted and would be handled identically to a
   missing default value (issue #11)
 * dbsake frm-to-schema now handles MySQL 5.0 .frm files; Previously
   frm-to-schema would attempt to read a non-existent partitioning clause and
   fail. (issue #14)

 * dbsake mysql-sandbox now auto-detects innodb-data-file-path based on
   existing ibdata* files from --data-source, or uses MySQL default
   if this is an empty sandbox instance (issue #12)
 * dbsake mysql-sandbox now handles invalid mysqld binaries more gracefully;
   This may occur if attempting to run i686 on an x86_64 platform for
   instance.  Previously this would fail on an ENOENT error and an uncaught
   exception would be thrown. (issue #13)
 * dbsake mysql-sandbox --sandbox-directory now handles relatives paths;
   Previously these were passed as-is to mysql which would reevaluate the
   path relative to the sandbox directory and typically fail to start
   (issue #15)


1.0.5 (2014-01-31)
------------------

New features:

 * dbsake mysql-sandbox's generated ./sandbox.sh script now supports an
   'upgrade' action to run mysql_upgrade against the sandbox instance.
   (issue #1)
 * dbsake mysql-sandbox --mysql-distribution=system (the default) now only
   copies the mysqld binary and assumes all other utilities are in the path;
   mysqld is copied to avoid security issues under apparmor in debuntu
   environments
 * dbsake mysql-sandbox has reduced the required disk footprint of mysql
   distribution tarballs by excluding ./bin/\*_embedded and ./bin/mysql-debug
   binaries in addition to excluding ./mysql-test, ./include and ./sql-bench
   that was done previously.
 * dbsake mysql-sandbox --data-source now supports directory paths, which
   point to an existing MySQL datadir; This option simply symlinks the
   specified directory to the sandbox ./data path.  Sandbox creation will
   fail if any of the standard InnoDB data/log files are locked indicating
   they are already used by another active instance.
 * dbsake mysql-sandbox will now set the root@localhost plugin to
   'mysql_native_password' when setting a password.  This avoids an issue
   with MySQL 5.7 which refuses authentication if plugin is not set, which
   may be the case if a sandbox is loaded with data from an earlier version.
 * dbsake mysql-sandbox now checks for libaio as part of the setup process
   and will abort if this is not available for MySQL 5.5+; This check can be
   disabled with the --skip-libcheck option, but if mysqld requires this
   library the sandbox creation will still fail in this case.
 * dbsake mysql-sandbox now performs gpg verification against downloaded
   mysql distribution tarballs using mysql.com's public key; This behavior
   can be disabled by using the new --skip-gpgcheck option
 * dbsake mysql-sandbox's generated ./sandbox.sh script now supports a
   'metadata' action for dumping information about the sandbox environment
 * dbsake mysql-sandbox's generated ./sandbox.sh script now supports a
   'version' action to echo the mysql version the sandbox was installed with

Bugs fixed:

 * dbsake mysql-sandbox no longer suppresses stderr when running mysqld
   --version; This is done to discover the exact version of the deployed
   mysql distribution to allow my.cnf generation to make adjustments based
   on the features available.
 * dbsake mysql-sandbox's generated ./sandbox.sh script now accepts extra
   commandline options for the 'restart' action which behaves identically
   to the 'start' action - these are passed down to the mysqld_safe script


1.0.4 (2014-01-24)
------------------

New features:

 * dbsake now handles SIGINT gracefully
 * dbsake now logs a cleaner format
 * dbsake --log-level option removed; --debug / --quiet options were added as
   simpler knobs to tweak logging output
 * dbsake now longer depends on argparse and it has been removed from the
   source tree

 * dbsake mysql-sandbox has renamed the --mysql-source option to
   --mysql-distribution; the short option (-m) is unchanged
 * dbsake mysql-sandbox --data-source|-D <path> option added with support for
   LVM and xtrabackup tarballs
 * dbsake mysql-sandbox --table|-t / --exclude-table|-T <pattern> option added
   to filter files read from --data-source tarballs
 * dbsake mysql-sandbox --cache-policy option added to support caching
   downloaded MySQL distribution tarballs
 * dbsake mysql-sandbox now supports a progress bar when downloading mysql
   tarball distributions and when extracting --data-source tarballs; The
   progress bar is only displayed when stderr is attached to a tty
 * dbsake mysql-sandbox now emits timing information for each major step in
   the sandbox creation process
 * dbsake mysql-sandbox's generated ./sandbox.sh script now supports 'use' and
   'mysql' actions for connecting to the sandbox instance; These are aliases
   for the 'shell' command included in v1.0.3
 * dbsake mysql-sandbox's generated ./sandbox.sh script now supports a
   'mysqldump' action for trivially running mysqldump against the sandbox
   instance
 * dbsake mysql-sandbox's generated ./sandbox.sh script now supports
   arguments for the 'start' action - these are passed directly to the
   mysqld_safe process to enable additional mysql options on startup
 * dbsake mysql-sandbox's generated ./sandbox.sh script now supports an
   'install-service' action that will deploy the ./sandbox.sh as a standard
   SysV initscript

Bugs fixed:

 * dbsake mysql-sandbox no longer prunes users in the sandbox to avoid removing
   existing users from user-provided --data-source tarballs


1.0.3 (2014-01-16)
------------------

New features:

 * third-party sarge [1]_ package added to dbsake tree
 * third-party tempita [2]_ package added to dbsake tree
 * dbsake now "lazy loads" imports for most commands to improve initial startup
   times
 * dbsake mysql-sandbox command added; see documentation for more details

.. [1] https://pypi.python.org/pypi/sarge/0.1.3
.. [2] https://pypi.python.org/pypi/Tempita/0.5.3dev

Bugs fixed:

 * dbsake frm-to-schema now supports very old VARCHAR fields
   (MYSQL_TYPE_VAR_STRING)
 * dbsake.spec now supports building under EPEL 5 environments


1.0.2 (2014-01-07)
------------------

New features:

 * dbsake frm-to-schema now parses views from plaintext .frm files
 * dbsake frm-to-schema --replace option added; This outputs view definitions
   as CREATE OR REPLACE view to ease importing into MySQL
 * dbsake frm-to-schema --raw-types option added; This adds comments to the
   column output indicating the low-level raw mysql type
   (e.g. MYSQL_TYPE_TINYBLOB) - previously these were always displayed
 * dbsake frm-to-schema now outputs a mysqldump-like comment block before each
   table or view's DDL

Bugs fixed:

 * dbsake frm-to-schema now formats prefix indexes correctly
 * dbsake frm-to-schema no longer outputs MYSQL_TYPE\_\* comments in CREATE
   TABLE output by default; use the new --raw-types to see this information.

1.0.1 (2014-01-06)
------------------

New features:
rename CHANGES.rst -> HISTORY.rst

 * dbsake --version/-V option added
 * documentation has been added to the project

Bugs fixed:

 * dbsake --log-level now recognizes log level names correctly
 * dbsake fincore now handles zero-byte files gracefully
 * dbsake fincore now releases mmap resources gracefully
 * dbsake {fincore,uncache} now skip paths that are not a regular file
 * dbsake.spec RPM spec now properly depends on python-setuptools

1.0.0 (2014-01-02)
------------------

 * First release of dbsake
