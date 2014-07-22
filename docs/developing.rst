.. _contributing:

Contributing to dbsake
----------------------
dbsake is maintained at https://github.com/abg/dbsake

Contributions are welcome.  To contribute fork the repo and send a pull
request.

Setting up a development environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

I recommend using virtualenvwrapper for development.  This is available through
OS packages on debian or redhat based distributions.

There are many ways to configure this, but this is how I setup my environment:

.. code-block:: bash
    
    $ sudo yum install python-virtualenvwrapper
    $ cat >> ~/.bashrc <<<". /usr/bin/virtualenvwrapper_lazy.sh"
    $ . ~/.bashrc
    $ mkvirtualenv dbsake
    $ workon dbsake
    $ cd ~/projects/
    $ git clone git@github.com:abg/dbsake.git
    $ cd dbsake
    $ python setup.py develop
    $ dbsake --help

Coding conventions
~~~~~~~~~~~~~~~~~~

* Follows PEP-8 as closely as possible
* Imports are sorted alphabetically and split into sections:

  * python stdlib imports
  * 3rd party imports (e.g. import MySQLdb)
  * dbsake imports

* Lines should be < 80 characters
