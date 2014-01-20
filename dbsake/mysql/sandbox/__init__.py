"""
dbsake.mysql.sandbox
~~~~~~~~~~~~~~~~~~~~

MySQL sandboxing support

"""
from __future__ import print_function

import os

from dbsake import baker

@baker.command(name='mysql-sandbox',
               shortopts={ 'sandbox_directory'  : 'd',
                           'mysql_distribution' : 'm',
                           'data_source'        : 'D',
                           'table'              : 't',
                           'exclude_table'      : 'T',
                           'cache_policy'       : 'c'},
               multiopts=['table', 'exclude_table'])
def mysql_sandbox(sandbox_directory=None,
                  mysql_distribution='system',
                  data_source=None,
                  table=(),
                  exclude_table=(),
                  cache_policy='always'):
    """
    Useful docstring here

    :param sandbox_directory: base directory where sandbox will be installed
    :param mysql_distribution: what mysql distribution to use for the sandbox;
                               This defaults to 'system' and this command will
                               attempt to use the currently installed mysql
                               distribution on the system.
    :param data_source: how to populate the sandbox; this defaults to
                        bootstrapping an empty mysql instance with a randomly
                        generated password for the root@localhost user.
    :param table: table to include from the data source
    :param exclude_table: table to exclude from data source;
    :param cache_policy: the cache policy to use when downloading an mysql
                         distribution
    """
    from . import common
    from . import datasource
    from . import distribution

    sbopts = common.check_options(**locals())

    common.prepare_sandbox_paths(sbopts)
    # Note here that loading from mysqldump sources cannot be done
    # until after the sandbox is bootstrapped
    # And generating defaults cannot be done until we have an innodb-log-file-size
    datasource.preload(sbopts)
    dist = distribution.deploy(sbopts)
    common.generate_defaults(os.path.join(sbopts.basedir, 'my.sandbox.cnf'),
                             user='root',
                             password=common.mkpassword(),
                             system_user=os.environ['USER'],
                             basedir=dist.basedir,
                             datadir=os.path.join(sbopts.basedir, 'data'),
                             socket=os.path.join(sbopts.basedir, 'data'),
                             tmpdir=os.path.join(sbopts.basedir, 'tmp'),
                             mysql_version=dist.version,
                             innodb_log_file_size=None,
                            )
    common.bootstrap(sbopts, dist)
    #data = datasource.postload(sbopts)

    return 0
