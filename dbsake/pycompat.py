"""
dbsake.pycompat
~~~~~~~~~~~~~~~

Python 2/3 compatbility code

"""
from __future__ import unicode_literals

import collections
import errno
import grp
import os
import pwd
import sys

PY3 = sys.version_info[0] == 3

if PY3:
    string_types = str,
    text_type = str
else:
    string_types = basestring,  # noqa
    text_type = unicode  # noqa


def _get_gid(name):
    """Returns a gid, given a group name."""
    if grp.getgrnam is None or name is None:
        return None
    try:
        result = grp.getgrnam(name)
    except KeyError:
        result = None
    if result is not None:
        return result[2]
    return None


def _get_uid(name):
    """Returns an uid, given a user name."""
    if pwd.getpwnam is None or name is None:
        return None
    try:
        result = pwd.getpwnam(name)
    except KeyError:
        result = None
    if result is not None:
        return result[2]
    return None


def chown(path, user=None, group=None):
    """Change owner user and group of the given path.

    user and group can be the uid/gid or the user/group names, and in that
    case, they are converted to their respective uid/gid.
    """

    if user is None and group is None:
        raise ValueError("user and/or group must be set")

    if not PY3 and isinstance(user, text_type):
        user = user.encode('utf-8')
    if not PY3 and isinstance(group, text_type):
        group = group.encode('utf-8')

    _user = user
    _group = group

    # -1 means don't change it
    if user is None:
        _user = -1
    # user can either be an int (the uid) or a string (the system username)
    elif isinstance(user, string_types):
        _user = _get_uid(user)
        if _user is None:
            raise LookupError("no such user: {0!r}".format(user))

    if group is None:
        _group = -1
    elif not isinstance(group, int):
        _group = _get_gid(group)
        if _group is None:
            raise LookupError("no such group: {0!r}".format(group))

    if not isinstance(_user, int):
        raise TypeError("Expected integer user, but got %s" %
                        type(_user).__name__)
    if not isinstance(_group, int):
        raise TypeError("Expected integer group, but got %s" %
                        type(_group).__name__)

    os.chown(path, _user, _group)


_ntuple_diskusage = collections.namedtuple('usage', 'total used free')


def disk_usage(path):
    """Return disk usage statistics about the given path.

    Return value is a named tuple with attributes 'total', 'used' and
    'free', which are the amount of total, used and free space, in bytes.
    """
    stv = os.statvfs(path)
    free = stv.f_bavail * stv.f_frsize
    total = stv.f_blocks * stv.f_frsize
    used = (stv.f_blocks - stv.f_bfree) * stv.f_frsize
    return _ntuple_diskusage(total, used, free)


def makedirs(name, mode=0o777, exist_ok=False):
    """makedirs(name [, mode=0o777][, exist_ok=False])

    Super-mkdir; create a leaf directory and all intermediate ones.  Works like
    mkdir, except that any intermediate path segment (not just the rightmost)
    will be created if it does not exist. If the target directory already
    exists, raise an OSError if exist_ok is False. Otherwise no exception is
    raised.  This is recursive.

    """
    head, tail = os.path.split(name)
    if not tail:
        head, tail = os.path.split(head)
    if head and tail and not os.path.exists(head):
        try:
            makedirs(head, mode, exist_ok)
        except OSError as exc:
            # be happy if someone already created the path
            if exc.errno != errno.EEXIST:
                raise
        cdir = os.curdir
        if PY3 and isinstance(tail, bytes):
            cdir = os.curdir.encode('ASCII')
        if tail == cdir:           # xxx/newdir/. exists if xxx/newdir exists
            return
    try:
        os.mkdir(name, mode)
    except OSError as e:
        if not exist_ok or e.errno != errno.EEXIST or not os.path.isdir(name):
            raise


# backport from py2.7.  patched to support paths relative to /
def relpath(path, start=os.curdir):
    """Return a relative version of a path"""
    sep = os.sep
    curdir = os.curdir
    pardir = os.pardir
    commonprefix = os.path.commonprefix
    abspath = os.path.abspath
    join = os.path.join

    if not path:
        raise ValueError("no path specified")

    start_list = [x for x in abspath(start).split(sep) if x]
    path_list = [x for x in abspath(path).split(sep) if x]

    # Work out how much of the filepath is shared by start and path.
    i = len(commonprefix([start_list, path_list]))

    rel_list = [pardir] * (len(start_list)-i) + path_list[i:]
    if not rel_list:
        return curdir
    return join(*rel_list)


def which(cmd, mode=os.F_OK | os.X_OK, path=None):
    """Given a command, mode, and a PATH string, return the path which
    conforms to the given mode on the PATH, or None if there is no such
    file.

    `mode` defaults to os.F_OK | os.X_OK. `path` defaults to the result
    of os.environ.get("PATH"), or can be overridden with a custom search
    path.

    """
    def _access_check(filename, mode):
        """
        Check that a given file can be accessed with the correct mode.
        Additionally check that `file` is not a directory, as on Windows
        directories pass the os.access check.
        """
        return (os.path.exists(filename) and os.access(filename, mode) and
                not os.path.isdir(filename))

    # If we're given a path with a directory part, look it up directly rather
    # than referring to PATH directories. This includes checking relative to
    # the current directory, e.g. ./script
    if os.path.dirname(cmd):
        if _access_check(cmd, mode):
            return cmd
        return None

    if path is None:
        path = os.environ.get("PATH", os.defpath)
    if not path:
        return None
    path = path.split(os.pathsep)

    if sys.platform == "win32":  # pragma: no cover
        # The current directory takes precedence on Windows.
        if os.curdir not in path:
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
    for dirpath in path:
        normdir = os.path.normcase(dirpath)
        if normdir not in seen:
            seen.add(normdir)
            for thefile in files:
                name = os.path.join(dirpath, thefile)
                if _access_check(name, mode):
                    return name
    return None


try:
    from contextlib import ExitStack
except ImportError:
    import collections

    # Inspired by discussions on http://bugs.python.org/issue13585
    class ExitStack(object):
        """Context manager for dynamic management of a stack of exit callbacks

        For example:

            with ExitStack() as stack:
              files = [stack.enter_context(open(fname)) for fname in filenames]
              # All opened files will automatically be closed at the end of
              # the with statement, even if attempts to open files later
              # in the list throw an exception

        """
        def __init__(self):
            self._exit_callbacks = collections.deque()

        def pop_all(self):
            "Preserve the context stack by transferring it to a new instance"
            new_stack = type(self)()
            new_stack._exit_callbacks = self._exit_callbacks
            self._exit_callbacks = collections.deque()
            return new_stack

        def _push_cm_exit(self, cm, cm_exit):
            """Helper to correctly register callbacks to __exit__ methods"""
            def _exit_wrapper(*exc_details):
                return cm_exit(cm, *exc_details)
            _exit_wrapper.__self__ = cm
            self.push(_exit_wrapper)

        def push(self, exit):
            """Registers a callback with the standard __exit__ method signature

            Can suppress exceptions the same way __exit__ methods can.

            Also accepts any object with an __exit__ method (registering the
            method instead of the object itself)
            """
            # We use an unbound method rather than a bound method to follow
            # the standard lookup behaviour for special methods
            _cb_type = type(exit)
            try:
                exit_method = _cb_type.__exit__
            except AttributeError:
                # Not a context manager, so assume its a callable
                self._exit_callbacks.append(exit)
            else:
                self._push_cm_exit(exit, exit_method)
            return exit  # Allow use as a decorator

        def callback(self, callback, *args, **kwds):
            """Registers an arbitrary callback and arguments.

            Cannot suppress exceptions.
            """
            def _exit_wrapper(exc_type, exc, tb):
                callback(*args, **kwds)
            # We changed the signature, so using @wraps is not appropriate, but
            # setting __wrapped__ may still help with introspection
            _exit_wrapper.__wrapped__ = callback
            self.push(_exit_wrapper)
            return callback  # Allow use as a decorator

        def enter_context(self, cm):
            """Enters the supplied context manager

            If successful, also pushes its __exit__ method as a callback and
            returns the result of the __enter__ method.
            """
            # We look up the special methods on the type to match
            # the with statement
            _cm_type = type(cm)
            _exit = _cm_type.__exit__
            result = _cm_type.__enter__(cm)
            self._push_cm_exit(cm, _exit)
            return result

        def close(self):
            """Immediately unwind the context stack"""
            self.__exit__(None, None, None)

        def __enter__(self):
            return self

        def __exit__(self, *exc_details):
            if not self._exit_callbacks:
                return

            # This looks complicated, but it is really just
            # setting up a chain of try-expect statements to ensure
            # that outer callbacks still get invoked even if an
            # inner one throws an exception
            def _invoke_next_callback(exc_details):
                # Callbacks are removed from the list in FIFO order
                # but the recursion means they're invoked in LIFO order
                cb = self._exit_callbacks.popleft()
                if not self._exit_callbacks:
                    # Innermost callback is invoked directly
                    return cb(*exc_details)
                # More callbacks left, so descend another level in the stack
                try:
                    suppress_exc = _invoke_next_callback(exc_details)
                except:
                    suppress_exc = cb(*sys.exc_info())
                    # Check if this cb suppressed the inner exception
                    if not suppress_exc:
                        raise
                else:
                    # Check if inner cb suppressed the original exception
                    if suppress_exc:
                        exc_details = (None, None, None)
                    suppress_exc = cb(*exc_details) or suppress_exc
                return suppress_exc
            # Kick off the recursive chain
            return _invoke_next_callback(exc_details)
