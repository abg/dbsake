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

Writing a new command
~~~~~~~~~~~~~~~~~~~~~

dbsake uses a slightly patched version of Baker 1.3 to implement subcommands.
You can see the changes against Baker 1.3 in contrib/baker.patch in the
dbsake source tree.  Otherwise all baker documentation applies to writing
subcommands for dbsake.

A new subcommand can be added by simply creating some submodule/subpackage
under dbsake/ and implementing a python function.  The return value of that
function is used as the exit status of dbsake.

For example if you could create a new example command by putting the following
in dbsake/mycmd.py:

.. code-block:: python

    """
    My new dbsake command
    """
    # import dbsake's version of baker
    from dbsake import baker

    @baker.command
    def mycommand(arg1='foo', arg2='bar'):
        """Run mycommand

        Example:
        # dbsake mycommand --arg1=foo --arg2=bar
        "--arg1='foo' --arg2='bar'"
        # echo $?
        42

        :param arg1: The first option to mycommand (default: 'foo')
        :param arg2: The second option to mycommand (default 'bar')
        """
        print "--arg1=%r --arg2=%r" % (arg1, arg2)
        return 42

You can run the command if you have dbsake setup properly in your environment:

.. code-block:: bash

   # dbsake mycommand --help
   Usage: dbsake mycommand [<arg1>] [<arg2>]
 
   Run mycommand
   
       Example: # dbsake mycommand --arg1=foo --arg2=bar "--arg1='foo'
       --arg2='bar'" # echo $? 42
   
   Options:
   
      --arg1  The first option to mycommand (default: 'foo')
      --arg2  The second option to mycommand (default 'bar')


