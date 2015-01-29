upgrade-mycnf
-------------

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

   $ dbsake upgrade-mycnf -t 5.6 --patch -c /etc/my.cnf
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
