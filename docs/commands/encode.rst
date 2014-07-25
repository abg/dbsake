encode
------

Encode a MySQL tablename with the MySQL filename encoding

This is the opposite of filename-to-tablename, where it takes a normal
tablename and converts it using MySQL's filename encoding.

Usage
.....

.. code-block:: bash

   Usage: dbsake encode [options] [NAMES]...

     Encode a MySQL tablename

   Options:
     -?, --help  Show this message and exit.

Example
.......

.. code-block:: bash

   $ dbsake encode foo.bar
   foo@002ebar

Options
.......

.. program:: encode

.. option:: path [path...]

   Specify a tablename to convert to an encoded filename
