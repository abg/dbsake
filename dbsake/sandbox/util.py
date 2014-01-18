import codecs
import collections
import errno
import os
import pkgutil
import random
import string
import sys
import tempfile

from dbsake.thirdparty import tempita
from dbsake.thirdparty import sarge

def escape(value):
    return value.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")

def load_template(name, **kwargs):
    kwargs.update(escape=escape)
    pkg = __name__.rpartition('.')[0]
    data = pkgutil.get_data(pkg, '/'.join(['templates', name]))
    return tempita.Template(data.decode("utf8"), namespace=kwargs)
 
def render_template(name, **kwargs):
    return load_template(name).substitute(**kwargs)
  
def mkpassword(length=8):
    alphabet = string.letters + string.digits + string.punctuation
    return ''.join(random.sample(alphabet, length))

def generate_defaults(path, metadata, **kwargs):
    # need to read a template to do this right
    template = load_template("my.sandbox.cnf")

    content = template.substitute(
        mysql_version=metadata.version,
        sandbox_root=path,
        basedir=metadata.basedir,
        mysql_user=os.environ['USER'],
        datadir=os.path.join(path, 'data'),
        socket=os.path.join(path, 'data', 'mysql.sock'),
        networking=False,
        additional_options=(),
        open_files_limit=1024,
        **kwargs
    )

    options_path = os.path.join(path, 'my.sandbox.cnf')
    with codecs.open(options_path, 'w', encoding='utf8') as fileobj:
        os.fchmod(fileobj.fileno(), 0660)
        fileobj.write(content)

    return options_path

def cat(path):
    with codecs.open(path, 'r', encoding='utf8') as fileobj:
        return fileobj.read()

def mysql_install_db(password, share_path='/usr/share/mysql'):
    join = os.path.join
    content = [
        render_template("bootstrap_initialize.sql"),
        cat(join(share_path, 'mysql_system_tables.sql')),
        cat(join(share_path, 'mysql_system_tables_data.sql')),
        cat(join(share_path, 'fill_help_tables.sql')),
        render_template("secure_mysql_installation.sql", password=password),
    ]
    return os.linesep.join(content)

def bootstrap_mysqld(mysqld, defaults_file, logfile, content):
    cmd = sarge.shell_format("{0} --defaults-file={1} --bootstrap -vvvvv",
                             mysqld, defaults_file)
    with open(logfile, 'wb') as stderr:
        with tempfile.TemporaryFile() as tmpfile:
            tmpfile.write(content.encode('utf8'))
            tmpfile.flush()
            tmpfile.seek(0)
            pipeline = sarge.run(cmd,
                                 input=tmpfile.fileno(),
                                 stdout=stderr,
                                 stderr=stderr)
    if sum(pipeline.returncodes) != 0:
        raise IOError(errno.EIO, "Bootstrap process failed")

def generate_initscript(sandbox_directory, **kwargs):
    content = render_template("sandbox.sh", 
                              sandbox_root=sandbox_directory,
                              **kwargs)

    sandbox_sh_path = os.path.join(sandbox_directory, 'sandbox.sh')
    with codecs.open(sandbox_sh_path, 'w', encoding='utf8') as fileobj:
        # ensure initscript is executable by current user + group
        os.fchmod(fileobj.fileno(), 0550)
        fileobj.write(content)
