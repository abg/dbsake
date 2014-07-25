uncache
-------

Remove a file's contents from the OS cache.

This command is useful when using O_DIRECT.  A file cached by the OS often
causes O_DIRECT to use a slower path - and often buffered + direct I/O is
an unsafe operation anyway.

With MySQL, for instance, a file may be accidentally cached by filesystem
backups that just archive all files under the MySQL datadir.  MySQL itself
may be using innodb-flush-method=O_DIRECT, and once these pages are cached
there can be a performance degradation.  uncache drops these cached pages
from the OS so O_DIRECT can work better.

Usage
.....

.. code-block:: bash

   Usage: dbsake uncache [OPTIONS] [PATHS]...

     Drop OS cached pages for a file.

   Options:
     -?, --help  Show this message and exit.

Example
.......

.. code-block:: bash

   # dbsake fincore /var/lib/mysql/ibdata1
   /var/lib/mysql/ibdata1: total_pages=6656 cached=6656 percent=100.00
   # dbsake uncache /var/lib/mysql/ibdata1
   Uncached /var/lib/mysql/ibdata1
   # dbsake fincore /var/lib/mysql/ibdata1
   /var/lib/mysql/ibdata1: total_pages=6656 cached=0 percent=0.00

Options
.......

.. program:: uncache

.. option:: path [path...]

   Path(s) to remove from cache.
