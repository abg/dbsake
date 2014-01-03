Subcommands
-----------

fincore
~~~~~~~

Discover which parts of a file are cached by the OS.

This command uses the mincore() system call on linux to grab a mapping of cached
pages.  Currently this done with a single mincore() call and requires 1-byte for
each 4KiB page.  For very large files, this may require several MiBs or more of
memory.  For a 1TB file this is 256MiB, for instance.

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

For example with the standard "mysql" database you might end up with a
set of files that look like the following:

.. code-block:: bash

    # tree mysql
    mysql/
        columns_priv.schema.sql.gz
        create.sql.gz
        db.schema.sql.gz
        event.schema.sql.gz
        func.schema.sql.gz
        general_log.schema.sql.gz
        help_category.schema.sql.gz
        help_keyword.schema.sql.gz
        help_relation.schema.sql.gz
        help_topic.schema.sql.gz
        host.schema.sql.gz
        innodb_index_stats.schema.sql.gz
        innodb_table_stats.schema.sql.gz
        ndb_binlog_index.schema.sql.gz
        plugin.schema.sql.gz
        proc.schema.sql.gz
        procs_priv.schema.sql.gz
        proxies_priv.schema.sql.gz
        servers.schema.sql.gz
        slave_master_info.schema.sql.gz
        slave_relay_log_info.schema.sql.gz
        slave_worker_info.schema.sql.gz
        slow_log.schema.sql.gz
        tables_priv.schema.sql.gz
        time_zone_leap_second.schema.sql.gz
        time_zone_name.schema.sql.gz
        time_zone.schema.sql.gz
        time_zone_transition.schema.sql.gz
        time_zone_transition_type.schema.sql.gz
        user.schema.sql.gz


.schema.sql* files include the table structure (CREATE TABLE)
.data.sql* files include the table data (INSERT INTO <table>)
create.sql* includes statements to recreate the database

If processing mysqldump --events --routines split-mysqldump will
additionally creates a routines.sql and events.sql files with the
correct content as needed.

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
   and set an appropriate suffix on its output files. E.g.
   -f gzip results in a .gz suffix, -f "bzip -9" results in
   .bz2 suffix, etc.

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

frm-to-schema
~~~~~~~~~~~~~

Decode a binary MySQL .frm file and output a CREATE TABLE statement.

This command does not require a MySQL server and interprets a .frm file
according to rules similar to the MySQL server.

.. important::
   This program only decodes data in the .frm file.  InnoDB foreign-key
   references are not preserved and AUTO_INCREMENT values are also not
   preserved as these are stored outside of the .frm.

.. program:: frm-to-schema

.. option:: path [path...]

   Specify the .frm files to generate a CREATE TABLE command from.


filename-to-tablename
~~~~~~~~~~~~~~~~~~~~~

Decode a MySQL encoded filename

As of MySQL 5.1, tablenames with special characters are encoded with a custom
"filename" encoding.  This command reverses that process to output the original
tablename.

.. program:: filename-to-tablename

.. option:: path [path...]

   Specify a filename to convert to plain unicode

tablename-to-filename
~~~~~~~~~~~~~~~~~~~~~

Encode a MySQL tablename with the MySQL filename encoding

This is the opposite of filename-to-tablename, where it takes a normal
tablename and converts it using MySQL's filename encoding.

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

.. program:: read-ib-binlog

.. option:: path

   Specify the path to a shared InnoDB tablespace (e.g. /var/lib/mysql/ibdata1)
   Binary log information will be read from this file.

