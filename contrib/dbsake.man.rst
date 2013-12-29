========
 dbsake
========

------------------------------
MySQL administration utilities
------------------------------

:Author: andrew.garner@rackspace.com
:Date:   2013-11-11
:Copyright: GPLv2
:Version: 1.0.0
:Manual section: 1
:Manual group: MySQL tools

.. TODO: authors and author with name <email>

SYNOPSIS
========

dbsake [command] options

DESCRIPTION
===========

dbsake provides a set of tools for managing a MySQL database

* split-mysqldump - split up a single mysqldump .sql file into a file per object
* upgrade-mycnf - patch a my.cnf file to handle deprecated options
* frm-to-schema - generate CREATE TABLE statements from .frm files

OPTIONS
=======

--version, -V           Show this program's version number and exit.
--help, -h              Show this help message and exit.

PROBLEMS
========

1. frm-to-schema may not handle very old (pre 5.0) .frm files.
2. frm-to-schema does not handle all the quirks for MariaDB

SEE ALSO
========

* ``man man`` and ``man 7 man``

BUGS
====

