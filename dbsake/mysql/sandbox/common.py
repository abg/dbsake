"""
dbsake.mysql.sandbox.common
~~~~~~~~~~~~~~~~~~~~~~~~~~

Common API schtuff
"""

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

    if kwargs['data_source'] and DATASOURCE_CRE.match(kwargs['data_source']):
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
        os.fchmod(fileobj.fileno(), 0550)
        fileobj.write(content)
    info("    * Generated initscript in %.2f seconds", time.time() - start)

def generate_defaults(defaults_file, **kwargs):
    start = time.time()
    content = render_template('my.sandbox.cnf', **kwargs)

    with codecs.open(defaults_file, 'wb', encoding='utf8') as stream:
        os.fchmod(stream.fileno(), 0o0660)
        stream.write(content)
    info("    * Generated %s in %.2f seconds", defaults_file, time.time() - start)

def mysql_install_db(dist, password):
    join = os.path.join
    def cat(path):
        with codecs.open(path, 'r', 'utf8') as fileobj:
            return fileobj.read()

    content = [
        render_template("bootstrap_initialize.sql"),
        cat(join(dist.sharedir, 'mysql_system_tables.sql')),
        cat(join(dist.sharedir, 'mysql_system_tables_data.sql')),
        cat(join(dist.sharedir, 'fill_help_tables.sql')),
        render_template("secure_mysql_installation.sql", password=password),
    ]
    return os.linesep.join(content)

def bootstrap(options, dist, password):
    start = time.time()
    defaults_file = os.path.join(options.basedir, 'my.sandbox.cnf')
    logfile = os.path.join(options.basedir, 'bootstrap.log')
    info("    - Logging bootstrap output to %s", logfile)
    cmd = sarge.shell_format("{0} --defaults-file={1} --bootstrap",
                             dist.mysqld, defaults_file)
    with open(logfile, 'wb') as stderr:
        with tempfile.TemporaryFile() as tmpfile:
            tmpfile.write(mysql_install_db(dist, password).encode('utf8'))
            tmpfile.flush()
            tmpfile.seek(0)
            info("    - Generated bootstrap SQL")
            info("    - Running %s", cmd)
            pipeline = sarge.run(cmd,
                                 input=tmpfile.fileno(),
                                 stdout=stderr,
                                 stderr=stderr)
    if sum(pipeline.returncodes) != 0:
        raise SandboxError("Bootstrap process failed")
    info("    * Bootstrapped sandbox in %.2f seconds", time.time() - start)
