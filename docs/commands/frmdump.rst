frmdump
-------

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

   Usage: dbsake.sh frmdump [options] [path[, path...]]
   
     Dump schema from MySQL frm files.
   
   Options:
     -t, --type-codes
     -R, --replace
     -?, --help        Show this message and exit.


Example
.......

.. code-block:: bash

   $ dbsake frmdump --type-codes /var/lib/mysql/mysql/plugin.frm
   --
   -- Table structure for table `plugin`
   -- Created with MySQL Version 5.5.35
   --
   
   CREATE TABLE `plugin` (
     `name` varchar(64) NOT NULL DEFAULT ''  /* MYSQL_TYPE_VARCHAR */,
     `dl` varchar(128) NOT NULL DEFAULT ''  /* MYSQL_TYPE_VARCHAR */,
     PRIMARY KEY (`name`)
   ) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='MySQL plugins';


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

.. option:: -t, --type-codes

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

.. versionchanged:: 2.0.0
   The ``--raw-types`` option was renamed to :option:`frmdump --type-codes`.

.. versionadded:: 1.0.2
   The :option:`frmdump --replace` option
