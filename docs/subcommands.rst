Subcommands
-----------

fincore
~~~~~~~

Discover which parts of a file are cached by the OS.

This command uses the mincore() system call on linux to grab a mapping of cached
pages.  Currently this done with a single mincore() call and requires 1-byte for
each 4KiB page.  For very large files, this may require several MiBs or more of
memory.  For a 1TB file this is 256MiB, for instance.

.. code-block:: bash

   $ dbsake fincore /var/lib/mysql/ibdata1
   /var/lib/mysql/ibdata1: total_pages=37376 cached=0 percent=0.00
   $ cat /var/lib/mysql/ibdata1 > /dev/null
   $ dbsake fincore /var/lib/mysql/ibdata1
   /var/lib/mysql/ibdata1: total_pages=37376 cached=37376 percent=100.00

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

.. code-block:: bash

   $ dbsake fincore /var/lib/mysql/ibdata1
   /var/lib/mysql/ibdata1: total_pages=37376 cached=37376 percent=100.00
   $ dbsake uncache /var/lib/mysql/ibdata1
   Uncached /var/lib/mysql/ibdata1
   $ dbsake fincore /var/lib/mysql/ibdata1
   /var/lib/mysql/ibdata1: total_pages=37376 cached=0 percent=0.00

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

.. important::
   This program only decodes data strictly available in the .frm file.
   InnoDB foreign-key references are not preserved and AUTO_INCREMENT values
   are also not preserved as these are stored outside of the .frm.


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


.. program:: frm-to-schema

.. option:: --replace

   Output view as CREATE OR REPLACE so that running the DDL against MySQL will
   overwrite a view.

.. option:: --raw-types

   Add comment to base tables noting the underlying mysql type code
   as MYSQL_TYPE_<name>.

.. option:: path [path...]

   Specify the .frm files to generate a CREATE TABLE command from.

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

.. code-block:: bash

   $ dbsake filename-to-tablename $(basename /var/lib/mysql/test/foo@002ebar.frm .frm)
   foo.bar

.. program:: filename-to-tablename

.. option:: path [path...]

   Specify a filename to convert to plain unicode

tablename-to-filename
~~~~~~~~~~~~~~~~~~~~~

Encode a MySQL tablename with the MySQL filename encoding

This is the opposite of filename-to-tablename, where it takes a normal
tablename and converts it using MySQL's filename encoding.

.. code-block:: bash

   $ dbsake tablename-to-filename foo.bar
   foo@002ebar

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

.. code-block:: bash

   $ dbsake read-ib-binlog /var/lib/mysql/ibdata1
   CHANGE MASTER TO MASTER_LOG_FILE='mysqld-bin.000003', MASTER_LOG_POS=644905653;


.. program:: read-ib-binlog

.. option:: path

   Specify the path to a shared InnoDB tablespace (e.g. /var/lib/mysql/ibdata1)
   Binary log information will be read from this file.

