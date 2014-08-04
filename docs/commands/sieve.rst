sieve
-----

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
   
     Filter and transform mysqldump output.
   
     sieve can extract single tables from a mysqldump file and perform useful
     transformations, such as adding indexes after the table data is loaded for
     InnoDB tables, where such indexes can be created much more efficiently
     than the default incremental rebuild that mysqldump performs.
   
   Options:
     -F, --format <name>             Select the output format (directory, stream)
     -C, --directory <path>          Specify output directory when
                                     --format=directory
     -i, --input-file <path>         Specify input file to process instead of
                                     stdin
     -z, --compress-command <name>   Specify compression command when
                                     --format=directory
     -t, --table <glob>              Only output tables matching the given glob
                                     pattern
     -T, --exclude-table <glob>      Excludes tables matching the given glob
                                     pattern
     --defer-indexes                 Add secondary indexes after loading table
                                     data
     --defer-foreign-keys            Add foreign key constraints after loading
                                     table data
     --write-binlog / --no-write-binlog
                                     Include SQL_LOG_BIN = 0 in output to disable
                                     binlog
     --table-data / --no-table-data  Include/exclude table data from output
     --routines / --no-routines      Include / exclude database routines from
                                     output
     --triggers / --no-triggers      Include/exclude table triggers from output
     --master-data / --no-master-data
                                     Uncomment/comment CHANGE MASTER in input, if
                                     present
     -f, --force                     Force various behaviors in this command
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

.. option:: --write-binlog / --no-write-binlog

   If ``--disable-binlog`` is set, sieve will output a SET SQL_LOG_BIN=0 SQL
   command to the beginning of the dump to avoid writing to the binary log
   when reloading the resulting output.  Use the option with care, as the
   resulting dump will not replicate to a slave if this option is set.

.. versionadded:: 2.0.0

.. option:: --table-data / --no-table-data

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

.. option::  --routines / --no-routines

   Include or exclude routines from the output, if routines were found in
   the input file.  By default routines are not excluded and will ony be
   excluded if the --no-routines option is specified.  --routines can be
   used to cancel a previous --no-routines option.

.. versionadded:: 2.0.0

.. option:: --triggers / --no-triggers

   Include or exclude table triggers from the output, if triggers were
   found in the input file. By default triggers are included for any
   output tables (subject to table filtering).   --no-triggers will
   disable output for all triggers and --triggers can be used to
   cancel the effects of an earlier --no-triggers option.

.. option:: -f, --force

   The ``--force`` option will force output to be written to stdout even if it
   appears that this will write to an active terminal. This can be useful in
   cases when filtering the mysqldump output or when not outputing large
   amounts of data and want to read it directly on the terminal.
