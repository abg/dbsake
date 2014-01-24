Getting Started
---------------

A quick way to get started is to fetch dbsake from http://docs.dbsake.net/get/dbake

This is an executable .zip file - once downloaded you can run it via python or
make it executable and run it directly.

.. code-block:: bash

   $ wget http://docs.dbsake.net/get/dbsake
   $ python dbsake --help
   usage: dbsake [-h] [--version] [-l {warn,error,debug,info,warning,critical}]
                 ...
   
   positional arguments:
     cmd
   
   optional arguments:
     -h, --help            show this help message and exit
     --version, -V         show program's version number and exit
     -l {warn,error,debug,info,warning,critical}, --log-level {warn,error,debug,info,warning,critical}
                           Choose a log level; default: info

   $ chmod u+x dbsake
   $ ./dbsake
   Usage: ./dbsake COMMAND <options>
   
   Available commands:
    filename-to-tablename  Decode a MySQL tablename as a unicode name
    fincore                Check if a file is cached by the OS
    frm-to-schema          Decode a binary MySQl .frm file to DDL
    import-frm             Import a binary .frm as a MyISAM table
    read-ib-binlog         Extract binary log filename/position from ibdata
    split-mysqldump        Split mysqldump output into separate files
    tablename-to-filename  Encode a unicode tablename as a MySQL filename
    uncache                Uncache a file from the OS page cache
    upgrade-mycnf          Patch a my.cnf to a new MySQL version
   
   Use './dbsake <command> --help' for individual command help.

.. note::
   DBSake requires python2.6+ to run.  If you are on an older Linux
   distribution such as RHEL5 you may need to install python2.6 or
   above from third party repositories.

With dbsake download you can run any of its subcommands.  For instance if you
want to poke an frm and see its table structure you might use the
:ref:`frm-to-schema` command::

   $ sudo ./dbsake frm-to-schema /var/lib/mysql/mysql/plugin.frm
   --
   -- Created with MySQL Version 5.6.15
   --
   
   CREATE TABLE `plugin` (
     `name` varchar(64) NOT NULL /* MYSQL_TYPE_VARCHAR */ DEFAULT '',
     `dl` varchar(128) NOT NULL /* MYSQL_TYPE_VARCHAR */ DEFAULT '',
     PRIMARY KEY (`name`)
   ) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT 'MySQL plugins';

Reporting Bugs
--------------

If you find a bug in dbsake please report the issue on the dbsake
issue on github `here <https://github.com/abg/dbsake/issues/new>`_

If you know how to fix the problem feel free to fork dbsake
and submit a pull request.  See :ref:`contributing` for more
information.
