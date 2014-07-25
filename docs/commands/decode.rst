decode
------

Decode a MySQL encoded filename

As of MySQL 5.1, tablenames with special characters are encoded with a custom
"filename" encoding.  This command reverses that process to output the original
tablename.

Usage
~~~~~

.. code-block:: bash

   Usage: dbsake decode [options] [NAMES]...

     Decode a MySQL tablename as a unicode name.

   Options:
     -?, --help  Show this message and exit.

Example
.......

.. code-block:: bash

   $ dbsake decode $(basename /var/lib/mysql/test/foo@002ebar.frm .frm)
   foo.bar

Options
.......

.. program:: filename-to-tablename

.. option:: path [path...]

   Specify a filename to convert to plain unicode
