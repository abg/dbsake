fincore
-------

Discover which parts of a file are cached by the OS.

This command uses the mincore() system call on linux to grab a mapping of cached
pages.  Currently this done with a single mincore() call and requires 1-byte for
each 4KiB page.  For very large files, this may require several MiBs or more of
memory.  For a 1TB file this is 256MiB, for instance.

Usage
.....

.. code-block:: bash

   Usage: dbsake fincore [OPTIONS] [PATHS]...
   
     Report cached pages for a file.
   
   Options:
     -v, --verbose
     -?, --help     Show this message and exit.


Example
.......

.. code-block:: bash

   # dbsake fincore /var/lib/mysql/ibdata1
   /var/lib/mysql/ibdata1: total_pages=6656 cached=0 percent=0.00
   # cat /var/lib/mysql/ibdata1 > /dev/null
   # dbsake fincore /var/lib/mysql/ibdata1
   /var/lib/mysql/ibdata1: total_pages=6656 cached=6656 percent=100.00

Options
.......

.. program:: fincore

.. option:: --verbose

   Print each cached page number that is cached.

.. option:: path [path...]

   Path(s) to check for cached pages
