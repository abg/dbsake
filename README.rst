=================
    酒 dbsake
=================

.. image:: https://badge.fury.io/py/dbsake.png
   :target: http://badge.fury.io/py/dbsake

.. image:: https://travis-ci.org/abg/dbsake.png
   :target: https://travis-ci.org/abg/dbsake

.. image:: https://coveralls.io/repos/abg/dbsake/badge.png
   :target: https://coveralls.io/r/abg/dbsake

.. image:: https://pypip.in/d/dbsake/badge.png
   :target: https://crate.io/packages/dbsake?version=latest


dbsake - a (s)wiss-(a)rmy-(k)nif(e) for MySQL

* Free software: GPLv2
* Documentation: http://docs.dbsake.net.

Features
--------

* `Parsing MySQL .frm files and output DDL`_
* `Filtering and transforming mysqldump output`_
* `Patching a my.cnf to remove or convert deprecated options`_
* `Deploying a new standalone MySQL "sandbox" instance`_
* `Decoding/encoding MySQL filenames`_
* `Managing OS caching for a set of files`_


.. _Parsing MySQL .frm files and output DDL: http://docs.dbsake.net/subcommands.html#frmdump
.. _Filtering and transforming mysqldump output: http://docs.dbsake.net/subcommands.html#sieve
.. _Patching a my.cnf to remove or convert deprecated options: http://docs.dbsake.net/subcommands.html#upgrade-mycnf
.. _Deploying a new standalone MySQL "sandbox" instance: http://docs.dbsake.net/subcommands.html#mysql-sandbox
.. _Decoding/encoding MySQL filenames: http://docs.dbsake.net/subcommands.html#decode
.. _Managing OS caching for a set of files: http://docs.dbsake.net/subcommands.html#fincore

Dependencies
------------

- Requires python v2.6+
- jinja2 >= 2.2
- click >= 2.0

Reporting Bugs
--------------

If you find a bug in dbsake please report the issue on the dbsake issue on
`github <https://github.com/abg/dbsake/issues/new>`_

If you know how to fix the problem feel free to fork dbsake and submit a pull
request.  See CONTRIBUTING.rst for more information.


Quickstart
----------

You can fetch dbsake easily from get.dbsake.net::

    $ curl get.dbsake.net > dbsake

This is an executable python zipfile.  You can see the contents by running::

    $ unzip -l dbsake
    or
    $ python -mzipfile -l dbsake

You can run as a script by making it executable::


    $ chmod u+x dbsake

Run it with no arguments to see all possible commands::

    $ dbsake
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

"Upgrading" a my.cnf
====================

Here's how you might upgrade a MySQL 5.0 my.cnf to 5.5::

    $ dbsake upgrade-mycnf --target=5.5 --config=my.cnf --patch
    Rewriting option 'log-slow-queries'. Reason: Logging options changed in MySQL 5.1
    Removing option 'skip-external-locking'. Reason: Default behavior in MySQL 4.1+
    --- a/my.cnf
    +++ b/my.cnf
    @@ -26,7 +26,6 @@
     [mysqld]
     port       = 3306
     socket     = /var/run/mysqld/mysqld.sock
    -skip-external-locking
     key_buffer_size = 384M
     max_allowed_packet = 1M
     table_open_cache = 512
    @@ -127,7 +126,9 @@
     #innodb_log_buffer_size = 8M
     #innodb_flush_log_at_trx_commit = 1
     #innodb_lock_wait_timeout = 50
    -log-slow-queries = /var/lib/mysql/slow.log
    +slow-query-log = 1
    +slow-query-log-file = /var/lib/mysql/slow.log
    +log-slow-slave-statements

     [mysqldump]
     quick

Processing mysqldump output
===========================

Here's how you filter a single table from a mysqldump::

    $ mysqldump -A | dbsake sieve --force -t mysql.db
    -- MySQL dump 10.14  Distrib 5.5.38-MariaDB, for Linux (x86_64)
    --
    -- Host: localhost    Database:
    -- ------------------------------------------------------
    -- Server version   5.5.38-MariaDB-log

    /\*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT \*/;
    /\*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS \*/;
    /\*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION \*/;
    /\*!40101 SET NAMES utf8 \*/;
    /\*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE \*/;
    /\*!40103 SET TIME_ZONE='+00:00' \*/;
    /\*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 \*/;
    /\*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 \*/;
    /\*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' \*/;
    /\*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 \*/;

    --
    -- Table structure for table `db`
    --

    DROP TABLE IF EXISTS `db`;
    /\*!40101 SET @saved_cs_client     = @@character_set_client \*/;
    /\*!40101 SET character_set_client = utf8 \*/;
    CREATE TABLE `db` (
      `Host` char(60) COLLATE utf8_bin NOT NULL DEFAULT '',
      `Db` char(64) COLLATE utf8_bin NOT NULL DEFAULT '',
      `User` char(16) COLLATE utf8_bin NOT NULL DEFAULT '',
      `Select_priv` enum('N','Y') CHARACTER SET utf8 NOT NULL DEFAULT 'N',
      `Insert_priv` enum('N','Y') CHARACTER SET utf8 NOT NULL DEFAULT 'N',
      `Update_priv` enum('N','Y') CHARACTER SET utf8 NOT NULL DEFAULT 'N',
      `Delete_priv` enum('N','Y') CHARACTER SET utf8 NOT NULL DEFAULT 'N',
      `Create_priv` enum('N','Y') CHARACTER SET utf8 NOT NULL DEFAULT 'N',
      `Drop_priv` enum('N','Y') CHARACTER SET utf8 NOT NULL DEFAULT 'N',
      `Grant_priv` enum('N','Y') CHARACTER SET utf8 NOT NULL DEFAULT 'N',
      `References_priv` enum('N','Y') CHARACTER SET utf8 NOT NULL DEFAULT 'N',
      `Index_priv` enum('N','Y') CHARACTER SET utf8 NOT NULL DEFAULT 'N',
      `Alter_priv` enum('N','Y') CHARACTER SET utf8 NOT NULL DEFAULT 'N',
      `Create_tmp_table_priv` enum('N','Y') CHARACTER SET utf8 NOT NULL DEFAULT 'N',
      `Lock_tables_priv` enum('N','Y') CHARACTER SET utf8 NOT NULL DEFAULT 'N',
      `Create_view_priv` enum('N','Y') CHARACTER SET utf8 NOT NULL DEFAULT 'N',
      `Show_view_priv` enum('N','Y') CHARACTER SET utf8 NOT NULL DEFAULT 'N',
      `Create_routine_priv` enum('N','Y') CHARACTER SET utf8 NOT NULL DEFAULT 'N',
      `Alter_routine_priv` enum('N','Y') CHARACTER SET utf8 NOT NULL DEFAULT 'N',
      `Execute_priv` enum('N','Y') CHARACTER SET utf8 NOT NULL DEFAULT 'N',
      `Event_priv` enum('N','Y') CHARACTER SET utf8 NOT NULL DEFAULT 'N',
      `Trigger_priv` enum('N','Y') CHARACTER SET utf8 NOT NULL DEFAULT 'N',
      PRIMARY KEY (`Host`,`Db`,`User`),
      KEY `User` (`User`)
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='Database privileges';
    /\*!40101 SET character_set_client = @saved_cs_client \*/;

    --
    -- Dumping data for table `db`
    --

    LOCK TABLES `db` WRITE;
    /\*!40000 ALTER TABLE `db` DISABLE KEYS \*/;
    /\*!40000 ALTER TABLE `db` ENABLE KEYS \*/;
    UNLOCK TABLES;

    /\*!40103 SET TIME_ZONE=@OLD_TIME_ZONE \*/;

    /\*!40101 SET SQL_MODE=@OLD_SQL_MODE \*/;
    /\*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS \*/;
    /\*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS \*/;
    /\*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT \*/;
    /\*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS \*/;
    /\*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION \*/;
    /\*!40111 SET SQL_NOTES=@OLD_SQL_NOTES \*/;

    -- Dump completed on 2014-07-22 21:01:35

Deploying a MySQL sandbox instance
==================================

Here is how you create a MySQL 5.7.3-m13 instance::

    $ dbsake sandbox -m 5.7.3-m13
    Preparing sandbox instance: /home/localuser/sandboxes/sandbox_20140722_210338
      Creating sandbox directories
        * Created directories in 0.00 seconds
      Deploying MySQL distribution
        - Deploying MySQL 5.7.3-m13 from download
        - Using cached download /home/localuser/.dbsake/cache/mysql-5.7.3-m13-linux-glibc2.5-x86_64.tar.gz
        - Verifying gpg signature via: /usr/bin/gpg2 --verify /home/localuser/.dbsake/cache/mysql-5.7.3-m13-linux-glibc2.5-x86_64.tar.gz.asc -
        - Unpacking tar stream. This may take some time
    (100.00%)[========================================] 322.9MiB / 322.9MiB
        - GPG signature validated
        * Deployed MySQL distribution in 13.56 seconds
      Generating my.sandbox.cnf
        - Generated random password for sandbox user root@localhost
        * Generated /home/localuser/sandboxes/sandbox_20140722_210338/my.sandbox.cnf in 0.03 seconds
      Bootstrapping sandbox instance
        - Logging bootstrap output to /home/localuser/sandboxes/sandbox_20140722_210338/bootstrap.log
        * Bootstrapped sandbox in 2.67 seconds
      Creating sandbox.sh initscript
        * Generated initscript in 0.01 seconds
    Sandbox created in 16.28 seconds

    Here are some useful sandbox commands:
           Start sandbox: /home/localuser/sandboxes/sandbox_20140722_210338/sandbox.sh start
            Stop sandbox: /home/localuser/sandboxes/sandbox_20140722_210338/sandbox.sh stop
      Connect to sandbox: /home/localuser/sandboxes/sandbox_20140722_210338/sandbox.sh mysql <options>
       mysqldump sandbox: /home/localuser/sandboxes/sandbox_20140722_210338/sandbox.sh mysqldump <options>
    Install SysV service: /home/localuser/sandboxes/sandbox_20140722_210338/sandbox.sh install-service

The sandbox.sh script has some convenient commands for interacting with the sandbox too::

    $ /home/localuser/sandboxes/sandbox_20140722_210338/sandbox.sh start
    Starting sandbox: .[OK]

    $ /home/localuser/sandboxes/sandbox_20140722_210338/sandbox.sh mysql -e 'select @@datadir, @@version, @@version_comment\G'
    *************************** 1. row ***************************
            @@datadir: /home/localuser/sandboxes/sandbox_20140722_210338/data/
            @@version: 5.7.3-m13-log
    @@version_comment: MySQL Community Server (GPL)

The sandbox.sh script can also install itself, if you want to make the sandbox persistent::

    $ sudo /home/localuser/sandboxes/sandbox_20140722_210338/sandbox.sh install-service
    + /bin/cp /home/localuser/sandboxes/sandbox_20140722_210338/sandbox.sh /etc/init.d/mysql-5.7.3
    + /sbin/chkconfig --add mysql-5.7.3 && /sbin/chkconfig mysql-5.7.3 on
    Service installed in /etc/init.d/mysql-5.7.3 and added to default runlevels

Dumping the schema from MySQL .frm files
========================================

Here's an example dumping a normal table's .frm::

    $ sudo dbsake frmdump /var/lib/mysql/sakila/actor.frm
    --
    -- Table structure for table `actor`
    -- Created with MySQL Version 5.5.34
    --

    CREATE TABLE `actor` (
      `actor_id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
      `first_name` varchar(45) NOT NULL,
      `last_name` varchar(45) NOT NULL,
      `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`actor_id`),
      KEY `idx_actor_last_name` (`last_name`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8;

You can also format VIEW .frm files directly as well::

    $ sudo dbsake frmdump /var/lib/mysql/sakila/actor_info.frm
    --
    -- View:         actor_info
    -- Timestamp:    2014-01-18 18:22:54
    -- Stored MD5:   402b8673b0c61034644b5b286519d3f1
    -- Computed MD5: 402b8673b0c61034644b5b286519d3f1
    --

    CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY INVOKER VIEW `actor_info` AS select `a`.`actor_id` AS `actor_id`,`a`.`first_name` AS `first_name`,`a`.`last_name` AS `last_name`,group_concat(distinct concat(`c`.`name`,': ',(select group_concat(`f`.`title` order by `f`.`title` ASC separator ', ') from ((`sakila`.`film` `f` join `sakila`.`film_category` `fc` on((`f`.`film_id` = `fc`.`film_id`))) join `sakila`.`film_actor` `fa` on((`f`.`film_id` = `fa`.`film_id`))) where ((`fc`.`category_id` = `c`.`category_id`) and (`fa`.`actor_id` = `a`.`actor_id`)))) order by `c`.`name` ASC separator '; ') AS `film_info` from (((`sakila`.`actor` `a` left join `sakila`.`film_actor` `fa` on((`a`.`actor_id` = `fa`.`actor_id`))) left join `sakila`.`film_category` `fc` on((`fa`.`film_id` = `fc`.`film_id`))) left join `sakila`.`category` `c` on((`fc`.`category_id` = `c`.`category_id`))) group by `a`.`actor_id`,`a`.`first_name`,`a`.`last_name`;
