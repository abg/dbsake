"""
dbsake.util.cmd
~~~~~~~~~~~~~~~

Convenience utilities for running commands via subprocess
"""
# pylint: disable=W0142

import codecs
import collections
import contextlib
import os
import re
import shlex
import signal
import string
import subprocess
import sys
import tempfile

# py3 support shim
try:
    _basestring = basestring
    _unicode = unicode
except NameError:
    _basestring = str
    _unicode = str


class ProcessResult(collections.namedtuple('ProcessResult',
                                           'status stdout stderr')):
    @property
    def returncode(self):
        return self.status


class CommandError(Exception):
    """Base exception for shell commands run through this API"""


def shlex_split(cmdline):
    """Simple wrapper around shlex.split to handle unicode in python 2.X"""
    if sys.version_info < (3, 0) and isinstance(cmdline, _unicode):
        cmdline = cmdline.encode('utf-8')
    return shlex.split(cmdline)


def restore_sigpipe():
    """Restore normal SIGPIPE behavior before executing a command

    This function should be provided as the preexec_fn argument to subprocess
    module methods.
    """
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)


@contextlib.contextmanager
def run_async(cmd, **kwargs):
    """Asynchronously run a command in a context manager

    This run a command via subprocess.Popen and yields the process
    object.

    This will always wait for the process on exit.
    """
    if 'cwd' in kwargs:
        kwargs['cwd'] = os.path.join(os.getcwd(), kwargs['cwd'])
    if 'env' in kwargs:
        kwargs['env'] = dict(os.environ, **kwargs['env'])
    if isinstance(cmd, _basestring) and not kwargs.get('shell'):
        cmd = shlex_split(cmd)
    # restore sigpipe by default, unless explicitly disabled
    if kwargs.pop('restore_sigpipe', True):
        kwargs['preexec_fn'] = restore_sigpipe
    # close_fds by default unless explicitly disabled
    if kwargs.pop('close_fds', True):
        kwargs['close_fds'] = True

    stdio = [name
             for name in ('stdin', 'stdout', 'stderr')
             if kwargs.get(name) == subprocess.PIPE]
    try:
        process = subprocess.Popen(cmd, **kwargs)
    except OSError as exc:
        raise CommandError('[%d] %s' % (exc.errno, exc.strerror))
    try:
        yield process
    finally:
        # on exit, we close all pipes
        # assume reader has read all data in contextmanager
        # if they care about it
        for name in stdio:
            pipe = getattr(process, name, None)
            if pipe:
                pipe.close()
        process.wait()


def run(cmd, **kwargs):
    """Execute a commmand

    :param cmd: command to execute - should be either a string or a list of
                arguments to pass to os.execve
    :returns: status of executed command
    """
    stdio = [kwargs[name]
             for name in ('stdin', 'stdout', 'stderr') if name in kwargs]
    if subprocess.PIPE in stdio:
        raise CommandError("run() does not support PIPE for stdio")

    with run_async(cmd, **kwargs) as process:
        return process.wait()


def capture_stdout(cmd, encoding='utf8', **kwargs):
    """Run a command and capture its stdout"""
    with tempfile.TemporaryFile() as stdout:
        returncode = run(cmd, stdout=stdout, **kwargs)
        stdout.flush()
        stdout.seek(0)
        if encoding:
            stdout = codecs.getreader(encoding)(stdout)
        return ProcessResult(status=returncode,
                             stdout=stdout.read(),
                             stderr=None)

# include here, but not really used anywhere yet
# commenting out to avoid exposing an api
'''
def capture_combined(cmd, encoding='utf-8', **kwargs):
    """Run a command and capture stdout and stderr as a single stream"""
    with tempfile.TemporaryFile() as stdout:
        returncode = run(cmd,
                         stdout=stdout,
                         stderr=subprocess.STDOUT,
                         **kwargs)
        stdout.flush()
        stdout.seek(0)
        if encoding:
            stdout = codecs.getreader(encoding)(stdout)
        output = stdout.read().decode(encoding)
        return ProcessResult(status=returncode,
                             stdout=output,
                             stderr=output)
'''


def capture_both(cmd, encoding='utf-8', **kwargs):
    """Run a command and capture stdout and stdout separately"""
    with tempfile.TemporaryFile() as stdout:
        with tempfile.TemporaryFile() as stderr:
            returncode = run(cmd,
                             stdout=stdout,
                             stderr=stderr,
                             **kwargs)
            for fileobj in (stdout, stderr):
                fileobj.flush()
                fileobj.seek(0)
            if encoding:
                utf8_reader = codecs.getreader(encoding)
                stdout = utf8_reader(stdout)
                stderr = utf8_reader(stderr)
            return ProcessResult(status=returncode,
                                 stdout=stdout.read(),
                                 stderr=stderr.read())

# The following shell quoting is adapted from sarge
# with minor code cleanups

# This regex determines which shell input needs quoting
# because it may be unsafe
UNSAFE = re.compile(r'[^\w%+,./:=@-]')


def shell_quote(value):
    """
    Quote text so that it is safe for Posix command shells.

    For example, "*.py" would be converted to "'*.py'". If the text is
    considered safe it is returned unquoted.

    :param s: The value to quote
    :type s: str (or unicode on 2.x)
    :return: A safe version of the input, from the point of view of Posix
             command shells
    :rtype: The passed-in type
    """
    assert isinstance(value, _basestring)
    if not value:
        result = "''"
    elif len(value) >= 2 and (value[0], value[-1]) == ("'", "'"):
        result = '"%s"' % value.replace('"', r'\"')
    elif not UNSAFE.search(value):
        result = value
    else:
        result = "'{0}'".format(value.replace("'", "'\"'\"'"))
    return result


class ShellFormatter(string.Formatter):
    """
    This class overrides :class:`string.Formatter` to provide a custom
    :meth:`convert_field` method, which ensures that fields are quoted for
    safety using :func:`shell_quote`.
    """

    def convert_field(self, value, conversion):
        """
        Convert a field to text.

        If a conversion is specified (e.g. !s, !r), no quoting is performed.
        If *no* conversion is specified, the value is converted to string
        (using :func:`str`) and that value is quoted using :func:`shell_quote`
        before being returned.
        :param value: The value to be converted
        :type value: any
        :param conversion: The conversion to apply
        :type conversion: str (or None)
        :return: The converted value
        :rtype: str
        """
        if conversion is None:
            result = shell_quote(str(value))
        else:
            result = super(ShellFormatter, self).convert_field(value,
                                                               conversion)
        return result


def shell_format(fmt, *args, **kwargs):
    """
    Format a shell command with format placeholders and variables to fill
    those placeholders.

    Note: you must specify positional parameters explicitly, i.e. as {0}, {1}
    instead of {}, {}. Requiring the formatter to maintain its own counter can
    lead to thread safety issues unless a thread local is used to maintain
    the counter. It's not that hard to specify the values explicitly
    yourself :-)

    :param fmt: The shell command as a format string. Note that you will need
                to double up braces you want in the result, i.e. { -> {{ and
                } -> }}, due to the way :meth:`str.format` works.
    :type fmt: str, or unicode on 2.x
    :param args: Positional arguments for use with ``fmt``.
    :param kwargs: Keyword arguments for use with ``fmt``.
    :return: The formatted shell command, which should be safe for use in
             shells from the point of view of shell injection.
    :rtype: The type of ``fmt``.
    """
    return ShellFormatter().vformat(fmt, args, kwargs)


@contextlib.contextmanager
def piped_stdin(cmd, **kwargs):
    """Start a command and yield its stdin

    This runs as a contextmanager, starting a command and returning the
    command's stdin pipe.  This is meant to provide an easy way to run
    a command and programatically feed it input on stdin.
    """
    kwargs['stdin'] = subprocess.PIPE
    with run_async(cmd, **kwargs) as process:
        yield process.stdin
    if process.returncode != 0:
        raise CommandError("'%s' exited with non-zero status" % cmd)

# XXX: compatibility hack
stream_command = piped_stdin

@contextlib.contextmanager
def piped_stdout(command, **kwargs):
    """Start a command and yield its stdout

    This runs as a contextmanager, starting a command and returning
    the command's stdout pipe.  This is meant to provide an easy way to run a
    a command programatically process its output.
    """
    kwargs['stdout'] = subprocess.PIPE
    with run_async(command, **kwargs) as process:
        yield process.stdout
    if process.returncode != 0:
        raise CommandError("'%s' exited with non-zero status" % command)
