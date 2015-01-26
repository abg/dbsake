"""
dbsake.core.mysql.sandbox.common
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Common API schtuff
"""
from __future__ import print_function
from __future__ import unicode_literals

import codecs
import collections
import errno
import fcntl
import glob
import logging
import os
import random
import re
import string
import time

from dbsake import pycompat
from dbsake.util import cmd
from dbsake.util import template

from dbsake.core.mysql import frm

info = logging.info
warn = logging.warn
debug = logging.debug


class SandboxError(Exception):
    """Base sandbox exception"""

SandboxOptions = collections.namedtuple('SandboxOptions',
                                        ['basedir', 'datadir',
                                         'distribution', 'datasource',
                                         'include_tables', 'exclude_tables',
                                         'cache_policy',
                                         'skip_libcheck', 'skip_gpgcheck',
                                         'force', 'mysql_user', 'password',
                                         'innobackupex_options',
                                         'report_progress',
                                         ])


VERSION_CRE = re.compile(r'\d+[.]\d+[.]\d+')


def check_options(**kwargs):
    """Check sandbox options"""
    basedir = kwargs.pop('sandbox_directory')
    if not basedir:
        basedir = os.path.join('~',
                               'sandboxes',
                               'sandbox_' + time.strftime('%Y%m%d_%H%M%S'))
    basedir = os.path.abspath(os.path.expanduser(basedir))

    dist = kwargs.pop('mysql_distribution')
    if dist != 'system' and not (os.path.exists(dist) or
                                 VERSION_CRE.match(dist)):
            raise SandboxError("Invalid MySQL distribution '%s'" % dist)

    if kwargs['cache_policy'] not in ('always', 'never', 'local', 'refresh'):
        raise SandboxError("Unknown --cache-policy '%s'" %
                           kwargs['cache_policy'])

    if not kwargs.get('datadir'):
        kwargs['datadir'] = os.path.join(basedir, 'data')
    else:
        kwargs['datadir'] = os.path.normpath(kwargs['datadir'])

    check_mysql_datadir(kwargs['datadir'])

    password = kwargs.get('password', False)
    if not password:
        password = mkpassword(random.randint(13, 27))
        info("    - Generated random password for mysql user %s@localhost",
             kwargs['mysql_user'])

    return SandboxOptions(
        basedir=basedir,
        datadir=kwargs['datadir'],
        distribution=dist,
        datasource=kwargs['data_source'],
        include_tables=kwargs['include_tables'],
        exclude_tables=kwargs['exclude_tables'],
        cache_policy=kwargs['cache_policy'],
        skip_libcheck=kwargs['skip_libcheck'],
        skip_gpgcheck=kwargs['skip_gpgcheck'],
        force=kwargs['force'],
        mysql_user=kwargs['mysql_user'],
        password=password,
        innobackupex_options=kwargs['innobackupex_options'],
        report_progress=kwargs['report_progress'],
    )


def check_mysql_datadir(datadir, force=False):
    """Check the given path for a MySQL datadir

    If the datadir does not exist, it will be created

    If the datadir is not empty, this will check if ib_logfile0
    is in use (advisory locked).

    If all else fails, ensure at least a mysql/user.frm is present
    or the datadir is probably invalid.  This can still be overriden
    by a correct --force option.

    :param datadir: path to the new sandbox datadir
    :raises: SandboxError on error
    """
    exists = os.path.exists
    datadir = os.path.normpath(datadir)

    # datadir doesn't exist yet
    if not exists(datadir):
        # will create it later
        return

    # datadir exists, but is empty
    if exists(datadir) and not os.listdir(datadir):
        # will bootstrap it later
        return

    # check for ib_logfile0 and ensure it's not locked
    ib_logfile0 = os.path.join(datadir, 'ib_logfile0')
    # first check that this is not an active datadir
    try:
        with open(ib_logfile0, 'rb') as fileobj:
            fcntl.lockf(fileobj.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
    except IOError as exc:
        if exc.errno == errno.EAGAIN:
            msg = "%s locked. %s seems to be used by another process" % \
                (ib_logfile0, datadir)
            raise SandboxError(msg)
        # ignore errors from missing ib_logfile*, but raise unexpected IOError
        if exc.errno != errno.ENOENT:
            # This means ib_logfile0 either exists, or some more
            # serious access restriction
            raise SandboxError("Unable to read %s: %s" % (ib_logfile0, exc))

    # non-empty datadir, so ensure at least ib_logfile0 or mysql/user.frm
    mysql_user_frm = os.path.join(datadir, 'mysql', 'user.frm')
    if not exists(ib_logfile0) and not exists(mysql_user_frm):
        msg = "%s does not appear to be a valid MySQL datadir" % datadir
        if not force:
            raise SandboxError(msg)
        else:
            warn(msg)


def prepare_sandbox_paths(sbopts):
    start = time.time()
    for path in (sbopts.datadir, os.path.join(sbopts.basedir, 'tmp')):
        try:
            if pycompat.makedirs(path, exist_ok=True):
                info("    - Created %s", path)
        except OSError as exc:
            raise SandboxError("%s" % exc)
    info("    * Prepared sandbox in %.2f seconds", time.time() - start)

# create a jinja2 environment we can load templates from
template_loader = template.create_environment(__name__.rpartition('.')[0])


def mkpassword(length=8):
    """Generate a random password"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.sample(alphabet, length))


def generate_initscript(sandbox_directory, **kwargs):
    """Generate an init script"""
    start = time.time()
    template = template_loader.get_template('sandbox.sh')
    content = template.render(sandbox_root=sandbox_directory,
                              **kwargs)

    sandbox_sh_path = os.path.join(sandbox_directory, 'sandbox.sh')
    with codecs.open(sandbox_sh_path, 'w', encoding='utf8') as fileobj:
        # ensure initscript is executable by current user + group
        os.fchmod(fileobj.fileno(), 0o0755)
        fileobj.write(content)
        fileobj.write("\n")
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
    :param kwargs: options to be passed directly to the my.sandbox.cnf
                   template
    """
    start = time.time()
    defaults_file = os.path.join(options.basedir, 'my.sandbox.cnf')

    # Check for innodb-log-file-size
    ib_logfile0 = os.path.join(options.datadir, 'ib_logfile0')
    ib_logfile_size = None
    try:
        ib_logfile_size = os.path.getsize(ib_logfile0)
    except OSError:
        debug("    # No ib_logfile0 found")
    if ib_logfile_size:
        kwargs['innodb_log_file_size'] = _format_logsize(ib_logfile_size)
        info("    + Existing ib_logfile0 detected.")
        info("Setting innodb-log-file-size=%s", kwargs['innodb_log_file_size'])

    ibdata = []
    ibdata_pattern = os.path.join(options.datadir, 'ibdata*')
    for path in sorted(glob.glob(ibdata_pattern)):
        rpath = os.path.basename(path)
        ibdata.append(rpath + ':' + _format_logsize(os.stat(path).st_size))
    if ibdata:
        kwargs['innodb_data_file_path'] = ';'.join(ibdata) + ':autoextend'
        info("    + Found existing shared innodb tablespace: %s",
             kwargs['innodb_data_file_path'])
    else:
        kwargs['innodb_data_file_path'] = None

    # Check for innodb_log_files_in_group
    innodb_log_files_in_group = sum(1 for name in os.listdir(options.datadir)
                                    if name.startswith('ib_logfile'))
    if innodb_log_files_in_group > 2:
        kwargs['innodb_log_files_in_group'] = innodb_log_files_in_group
        info("    - Multiple ib_logfile* logs found.")
        info("    - Setting innodb-log-files-in-group=%s",
             kwargs['innodb_log_files_in_group'])
    else:
        kwargs['innodb_log_files_in_group'] = 2

    template = template_loader.get_template('my.sandbox.cnf')
    content = template.render(**kwargs)
    with codecs.open(defaults_file, 'wb', encoding='utf8') as stream:
        os.fchmod(stream.fileno(), 0o0660)
        stream.write(content)
        stream.write("\n")
    info("    * Generated %s in %.2f seconds",
         defaults_file, time.time() - start)
    return defaults_file


def user_grant_from_sql(options, mysql_system_tables_data):
    for line in mysql_system_tables_data.splitlines():
        if line.startswith("INSERT INTO tmp_user VALUES ('localhost'"):
            sql = line
            break
    else:
        raise SandboxError("Unable to generate mysql user grant")

    sql = sql.replace('INSERT', 'REPLACE', 1)
    sql = sql.replace('tmp_user', 'user', 1)
    sql = sql.replace("'root'",
                      "'%s'" % template.escape_string(options.mysql_user), 1)
    sql = sql.replace("''",
                      "PASSWORD('%s')" %
                      template.escape_string(options.password), 1)
    return sql


def user_grant_from_frm(options, distribution):
    user_frm = os.path.join(options.datadir, 'mysql', 'user.frm')
    debug("    # Parsing binary frm: %s", user_frm)
    table = frm.parse(user_frm)
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
            values.append("'%s'" % template.escape_string(options.mysql_user))
        elif column.name == 'Password':
            values.append("PASSWORD('%s')" %
                          template.escape_string(options.password))
        elif column.name == 'plugin':
            # Avoid setting mysql.user (plugin) field except for 5.7
            # MariaDB currently has very strange behaviors that can
            # lead to security problems if plugin is set.
            if distribution.version[0:2] == (5, 7):
                values.append("'mysql_native_password'")
            else:
                values.append("''")
        elif column.default is not None:
            values.append(column.default)
        else:
            values.append("''")

    return 'REPLACE INTO `user` ({names}) VALUES ({values});'.format(
        names=','.join("`{0}`".format(name) for name in names),
        values=','.join("{0}".format(value) for value in values)
    )


def mysql_install_db(options, distribution, **kwargs):
    join = os.path.join

    def cat(path):
        with codecs.open(path, 'r', 'utf8') as fileobj:
            return fileobj.read()

    sharedir = distribution.sharedir
    mysql_system_tables = cat(join(sharedir, 'mysql_system_tables.sql'))
    mysql_system_tables_data = cat(join(sharedir,
                                        'mysql_system_tables_data.sql'))
    try:
        # MariaDB uses a separate mysql_performance_tables.sql file
        p_s_sql_path = join(sharedir, 'mysql_performance_tables.sql')
        mysql_p_s_tables = cat(p_s_sql_path)
    except IOError as exc:
        if exc.errno != errno.ENOENT:
            raise
        mysql_p_s_tables = ''

    fill_help_tables = cat(join(sharedir, 'fill_help_tables.sql'))

    mysql_user_frm = os.path.join(options.datadir, 'mysql', 'user.frm')
    bootstrap_data = not os.path.exists(mysql_user_frm)
    if bootstrap_data:
        user_dml = user_grant_from_sql(options, mysql_system_tables_data)
    else:
        user_dml = user_grant_from_frm(options, distribution)

    template = template_loader.get_template('bootstrap.sql')
    sql = template.render(distribution=distribution,
                          mysql_system_tables=mysql_system_tables,
                          mysql_system_tables_data=mysql_system_tables_data,
                          mysql_performance_tables=mysql_p_s_tables,
                          fill_help_tables=fill_help_tables,
                          user_dml=user_dml,
                          **kwargs)
    for line in sql.splitlines():
        yield line


def bootstrap(options, distribution, additional_options=()):
    start = time.time()
    defaults_file = os.path.join(options.basedir, 'my.sandbox.cnf')
    logfile = os.path.join(options.basedir, 'bootstrap.log')
    info("    - Logging bootstrap output to %s", logfile)

    bootstrap_cmd = cmd.shell_format("{0} --defaults-file={1}",
                                     distribution.mysqld, defaults_file)
    additional_options = ('--bootstrap',
                          '--default-storage-engine=myisam') + \
        additional_options
    additional = ' '.join(map(cmd.shell_quote, additional_options))
    if additional:
        bootstrap_cmd += ' ' + additional

    bootstrap_sql = os.path.join(options.basedir, 'bootstrap.sql')
    with codecs.open(bootstrap_sql, 'wb', 'utf8') as fileobj:
        os.fchmod(fileobj.fileno(), 0o0660)
        for line in mysql_install_db(options, distribution):
            print(line, file=fileobj)
    info("    - Generated bootstrap SQL")
    with open(logfile, 'wb') as stderr:
        with open(bootstrap_sql, 'rb') as fileobj:
            info("    - Running %s", bootstrap_cmd)
            returncode = cmd.run(bootstrap_cmd,
                                 stdin=fileobj,
                                 stdout=stderr,
                                 stderr=stderr)
    if returncode != 0:
        raise SandboxError("Bootstrapping failed. Details in %s" % stderr.name)
    info("    * Bootstrapped sandbox in %.2f seconds", time.time() - start)
