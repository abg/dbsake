.. dbsake documentation master file, created by
   sphinx-quickstart on Fri Jan  3 17:50:49 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to dbsake
=================

.. image:: _static/sake-icon.png

dbsake is a collection of command-line tools to perform various DBA related
tasks for MySQL.

.. code-block:: bash

   # curl http://get.dbsake.net > dbsake
   # chmod u+x dbsake
   # mysqldump --all-databases | ./dbsake split-mysqldump -C /var/lib/backups/today/
   ...
   2014-01-03 21:01:15,228 Split input into 2 database(s) 35 table(s) and 0 view(s)

.. toctree::
   :maxdepth: 4
   
   readme
   subcommands
   developing
   frm_format
   history

Indices and tables
==================

.. only:: html

   * :ref:`genindex`
   * :ref:`search`
