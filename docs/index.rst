.. dbsake documentation master file, created by
   sphinx-quickstart on Fri Jan  3 17:50:49 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to DBSake
=================

DBSake is a collection of command-line tools to perform various DBA related
tasks for MySQL.

.. code-block:: bash

   # wget www.maybesql.net/get/dbsake
   # chmod u+x dbsake
   # mysqldump --all-databases | ./dbsake split-mysqldump -C /var/lib/backups/today/
   ...
   2014-01-03 21:01:15,228 Split input into 2 database(s) 35 table(s) and 0 view(s)

.. only:: html

   .. toctree::
      :maxdepth: 4
   
      getting_started
      subcommands
      developing
      frm_format

.. only:: man

   .. toctree::
      :maxdepth: 4
   
      getting_started
      subcommands

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
