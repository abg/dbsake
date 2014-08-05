Usage
=====

Synopsis
--------

 dbsake [-d|--debug] [-q|--quiet] [-V|--version] [-?|--help] <command> [<args>]

Description
-----------

dbsake is a collection of command-line tools to assist with administering parts
of a MySQL database.

Formatted and hyperlinked versions of the latest dbsake documentation can be
found at http://docs.dbsake.net.

Options
-------

.. program:: dbsake

.. option:: -?, --help

   Show the top-level dbsake options

.. option:: -V, --version

   Output the current dbsake version and exit

.. option:: -q, --quiet

   Suppresses all logging output.  Commands that output to stdout will still
   emit output, but no logging will be performed.  You can use the exit
   status of dbsake to detect failure in these cases

.. option:: -d, --debug

   Enable debugging output.  This enables more verbose logs that are typically
   not necessary, but may be helpful for troubleshooting.

Enabling Bash completion
------------------------

dbsake supports bash completion via the python-click library.  To enable this
you can run the following command::

  eval $(_DBSAKE_COMPLETE=source dbsake)

This will enable tab completing subcommands and options.

Bash completion only works if the script is run directly and not directly via
the python interpreter.  That is the following will use tab completion::

 # eval $(_DBSAKE_COMPLETE=source ./dbsake)
 # ./dbsake <TAB>

However, the following command will not::

 # eval $(_DBSAKE_COMPLETE=source dbsake)
 # python dbsake<TAB>
