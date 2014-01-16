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

def mkdir_p(path, *args):
    try:
        os.makedirs(path, *args)
        return True
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
    else:
        return False

def resolve_mountpoint(path):
    path = os.path.realpath(path)

    while path != os.path.sep:
        if os.path.ismount(path):
            return path
        path = os.path.abspath(os.path.join(path, os.pardir))
    return path

_ntuple_diskusage = collections.namedtuple('usage', 'total used free')

def disk_usage(path):
    """Return disk usage statistics about the given path.

    Return value is a named tuple with attributes 'total', 'used' and
    'free', which are the amount of total, used and free space, in bytes.
    """
    stat = os.statvfs(resolve_mountpoint(path))
    free = stat.f_bavail * stat.f_frsize
    total = stat.f_blocks * stat.f_frsize
    used = (stat.f_blocks - stat.f_bfree) * stat.f_frsize
    return _ntuple_diskusage(total, used, free)

def which(cmd, mode=os.F_OK | os.X_OK, path=None):
    """Given a command, mode, and a PATH string, return the path which
    conforms to the given mode on the PATH, or None if there is no such
    file.

    `mode` defaults to os.F_OK | os.X_OK. `path` defaults to the result
    of os.environ.get("PATH"), or can be overridden with a custom search
    path.

    """
    # Check that a given file can be accessed with the correct mode.
    # Additionally check that `file` is not a directory, as on Windows
    # directories pass the os.access check.
    def _access_check(fn, mode):
        return (os.path.exists(fn) and os.access(fn, mode)
                and not os.path.isdir(fn))

    # If we're given a path with a directory part, look it up directly rather
    # than referring to PATH directories. This includes checking relative to the
    # current directory, e.g. ./script
    if os.path.dirname(cmd):
        if _access_check(cmd, mode):
            return cmd
        return None

    if path is None:
        path = os.environ.get("PATH", os.defpath)
    if not path:
        return None
    path = path.split(os.pathsep)

    if sys.platform == "win32":
        # The current directory takes precedence on Windows.
        if not os.curdir in path:
            path.insert(0, os.curdir)

        # PATHEXT is necessary to check on Windows.
        pathext = os.environ.get("PATHEXT", "").split(os.pathsep)
        # See if the given file matches any of the expected path extensions.
        # This will allow us to short circuit when given "python.exe".
        # If it does match, only test that one, otherwise we have to try
        # others.
        if any(cmd.lower().endswith(ext.lower()) for ext in pathext):
            files = [cmd]
        else:
            files = [cmd + ext for ext in pathext]
    else:
        # On other platforms you don't have things like PATHEXT to tell you
        # what file suffixes are executable, so just pass on cmd as-is.
        files = [cmd]

    seen = set()
    for dir in path:
        normdir = os.path.normcase(dir)
        if not normdir in seen:
            seen.add(normdir)
            for thefile in files:
                name = os.path.join(dir, thefile)
                if _access_check(name, mode):
                    return name
    return None

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

def generate_defaults(path, user, password, metadata):
    # need to read a template to do this right
    template = load_template("my.sandbox.cnf")

    content = template.substitute(
        mysql_version=metadata.version,
        sandbox_root=path,
        basedir=metadata.basedir,
        mysql_user=os.environ['USER'],
        user=user,
        password=password,
        datadir=os.path.join(path, 'data'),
        socket=os.path.join(path, 'data', 'mysql.sock'),
        networking=False,
        additional_options=(),
        open_files_limit=1024,
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
