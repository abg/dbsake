"""
dbsake.mysql.sandbox.common
~~~~~~~~~~~~~~~~~~~~~~~~~~

Common API schtuff
"""
from __future__ import print_function

import codecs
import collections
import logging
import os
import random
import re
import string
import tempfile
import time

from dbsake.thirdparty import sarge
from dbsake.util import path
from dbsake.util import template

info = logging.info
warn = logging.warn
debug = logging.debug

class SandboxError(Exception):
    """Base sandbox exception"""

SandboxOptions = collections.namedtuple('SandboxOptions',
                                        ['basedir',
                                         'distribution', 'datasource',
                                         'tables', 'exclude_tables',
                                         'cache_policy',
                                        ])


VERSION_CRE = re.compile(r'\d+[.]\d+[.]\d+')

# only support gzip or bzip2 data sources for now
# may be either a tarball or a sql
DATASOURCE_CRE = re.compile(r'.*[.](tar|sql)([.](gz|bz2))?$')

def check_options(**kwargs):
    """Check sandbox options"""
    basedir = kwargs.pop('sandbox_directory')
    if not basedir:
        basedir = os.path.join('~',
                               'sandboxes',
                               'sandbox_' + time.strftime('%Y%m%d_%H%M%S'))
    basedir = os.path.normpath(os.path.expanduser(basedir))

    dist = kwargs.pop('mysql_distribution')
    if (dist != 'system' and
        not os.path.exists(dist) and
        not VERSION_CRE.match(dist)):
            raise SandboxError("Incoherent mysql distribution: %s" % dist)

    if kwargs['data_source'] and not DATASOURCE_CRE.match(kwargs['data_source']):
        raise SandboxError("Unsupported data source %s" %
                           kwargs['data_source'])

    if kwargs['cache_policy'] not in ('always', 'never', 'local', 'refresh'):
        raise SandboxError("Unknown --cache-policy '%s'" %
                           kwargs['cache_policy'])

    return SandboxOptions(
        basedir=basedir,
        distribution=dist,
        datasource=kwargs['data_source'],
        tables=kwargs['table'],
        exclude_tables=kwargs['exclude_table'],
        cache_policy=kwargs['cache_policy']
    )


def prepare_sandbox_paths(sbopts):
    start = time.time()
    for name in ('data', 'tmp'):
        if path.makedirs(os.path.join(sbopts.basedir, name)):
            info("    - Created %s/%s", sbopts.basedir, name)
    info("    * Prepared sandbox in %.2f seconds", time.time() - start)

# Template renderer that can load + render templates in the templates
# directory located in this package
render_template = template.loader(package=__name__.rpartition('.')[0],
                                       prefix='templates')


def mkpassword(length=8):
    """Generate a random password"""
    alphabet = string.letters + string.digits + string.punctuation
    return ''.join(random.sample(alphabet, length))

def generate_initscript(sandbox_directory, **kwargs):
    """Generate an init script"""
    start = time.time()
    content = render_template("sandbox.sh",
                              sandbox_root=sandbox_directory,
                              **kwargs)

    sandbox_sh_path = os.path.join(sandbox_directory, 'sandbox.sh')
    with codecs.open(sandbox_sh_path, 'w', encoding='utf8') as fileobj:
        # ensure initscript is executable by current user + group
        os.fchmod(fileobj.fileno(), 0o0755)
        fileobj.write(content)
    info("    * Generated initscript in %.2f seconds", time.time() - start)

def _format_logsize(value):
    if value % 1024**3 == 0:
        return '%dG' % (value // 1024**3)
    elif value % 1024**2 == 0:
        return '%dM' % (value // 1024**2)
    else:
        return '%d' % value

def generate_defaults(options, **kwargs):
    """Generate a my.sandbox.cnf file

    :param options: SandboxOptions instance
    :param **kwargs: options to be passed directly to the my.sandbox.cnf
                     template
    """
    start = time.time()
    defaults_file = os.path.join(options.basedir, 'my.sandbox.cnf')

    # Check for innodb-log-file-size
    try:
        ib_logfile0 = os.path.join(options.basedir, 'data', 'ib_logfile0')
        kwargs['innodb_log_file_size'] = _format_logsize(os.stat(ib_logfile0).st_size)
        info("    ! Existing ib_logfile0 detected. Setting innodb-log-file-size=%s",
             kwargs['innodb_log_file_size'])
    except OSError as exc:
        # ignore errors here
        pass

    # Check for innodb_log_files_in_group
    try:
        datadir = os.path.join(options.basedir, 'data')
        innodb_log_files_in_group = sum(1 for name in os.listdir(datadir)
                                          if name.startswith('ib_logfile'))
        if innodb_log_files_in_group > 2:
            kwargs['innodb_log_files_in_group'] = innodb_log_files_in_group
            info("    ! Multiple ib_logfile* logs found. Setting innodb-log-files-in-group=%s",
                 kwargs['innodb_log_files_in_group'])
    except OSError as exc:
        pass

    content = render_template('my.sandbox.cnf', **kwargs)
    with codecs.open(defaults_file, 'wb', encoding='utf8') as stream:
        os.fchmod(stream.fileno(), 0o0660)
        stream.write(content)
    info("    * Generated %s in %.2f seconds", defaults_file, time.time() - start)
    return defaults_file

def generate_sandbox_user_grant(datadir):
    from dbsake.mysql.frm import binaryfrm

    user_frm = os.path.join(datadir, 'mysql', 'user.frm')
    debug("    # Parsing binary frm: %s", user_frm)
    table = binaryfrm.parse(user_frm)
    debug("    # user.frm was created by MySQL %s", table.mysql_version)
    names = []
    values = []

    for column in table.columns:
        names.append(column.name)
        if column.name.endswith('_priv'):
            values.append("'Y'")
        elif column.name == 'Host':
            values.append("'localhost'")
        elif column.name == 'User':
            values.append("'root'")
        elif column.name == 'Password':
            # this gets reset later in the bootstrap process
            # initialize to a bad hash so at worst, the password
            # does not work
            values.append("'_invalid'")
        elif column.default is not None:
            values.append(column.default)
        else:
            values.append("''")

    return 'REPLACE INTO `user` ({names}) VALUES ({values});'.format(
        names=','.join("`{0}`".format(name) for name in names),
        values=','.join("{0}".format(value) for value in values)
    )

def mysql_install_db(distribution, **kwargs):
    join = os.path.join
    def cat(path):
        with codecs.open(path, 'r', 'utf8') as fileobj:
            return fileobj.read()

    sharedir = distribution.sharedir
    mysql_system_tables = cat(join(sharedir, 'mysql_system_tables.sql'))
    mysql_system_tables_data = cat(join(sharedir,
                                        'mysql_system_tables_data.sql'))
    fill_help_tables = cat(join(sharedir, 'fill_help_tables.sql'))

    sql = render_template('bootstrap.sql',
                          distribution=distribution,
                          mysql_system_tables=mysql_system_tables,
                          mysql_system_tables_data=mysql_system_tables_data,
                          fill_help_tables=fill_help_tables,
                          **kwargs)
    for line in sql.splitlines():
        yield line

def bootstrap(options, dist, password, additional_options=()):
    start = time.time()
    defaults_file = os.path.join(options.basedir, 'my.sandbox.cnf')
    logfile = os.path.join(options.basedir, 'bootstrap.log')
    info("    - Logging bootstrap output to %s", logfile)
    cmd = sarge.shell_format("{0} --defaults-file={1} --bootstrap",
                             dist.mysqld, defaults_file)
    additional = ' '.join(map(sarge.shell_format, additional_options))
    if additional:
        cmd += ' ' + additional

    datadir = os.path.join(options.basedir, 'data')
    user_dml = None
    if os.path.exists(os.path.join(datadir, 'mysql', 'user.frm')):
        info("    - User supplied mysql.user table detected.")
        info("    - Skipping normal load of system table data")
        info("    - Ensuring root@localhost exists")
        user_dml = generate_sandbox_user_grant(datadir)
        debug("    # DML: %s", user_dml)
        bootstrap_data = False
    else:
        info("    - Will bootstrap the mysql database")
        bootstrap_data = True # at least no user table

    bootstrap_sql = os.path.join(options.basedir, 'bootstrap.sql')
    with codecs.open(bootstrap_sql, 'wb', 'utf8') as fileobj:
        os.fchmod(fileobj.fileno(), 0o0660)
        for line in mysql_install_db(dist,
                                     bootstrap_data=bootstrap_data,
                                     password=password,
                                     user_dml=user_dml):
            print(line, file=fileobj)
    with open(logfile, 'wb') as stderr:
            info("    - Generated bootstrap SQL")
            info("    - Running %s", cmd)
            with open(bootstrap_sql, 'rb') as fileobj:
                pipeline = sarge.run(cmd,
                                     input=fileobj.fileno(),
                                     stdout=stderr,
                                     stderr=stderr)
    if sum(pipeline.returncodes) != 0:
        raise SandboxError("Bootstrapping failed. Details in %s" % stderr.name)
    info("    * Bootstrapped sandbox in %.2f seconds", time.time() - start)
