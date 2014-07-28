decode-tablename
----------------

Decode a MySQL encoded filename

As of MySQL 5.1, tablenames with special characters are encoded with a custom
"filename" encoding.  This command reverses that process to output the original
tablename.

Usage
~~~~~

.. code-block:: bash

   Usage: dbsake decode-tablename [options] [NAMES]...

     Decode a MySQL tablename as a unicode name.

   Options:
     -?, --help  Show this message and exit.

Example
.......

.. code-block:: bash

   $ dbsake decode-tablename foo@002ebar
   foo.bar

Options
.......

.. program:: decode-tablename

.. option:: path [path...]

   Specify a filename to convert to plain unicode
