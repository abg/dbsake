"""
dbsake.cli
~~~~~~~~~

Main dbsake cli entrypoint
"""
from __future__ import unicode_literals

import logging
import sys

import click

from dbsake import __version__ as dbsake_version

CONTEXT_SETTINGS = dict(help_option_names=['-?', '--help'])

try:
    NullHandler = logging.NullHandler
except AttributeError:
    class NullHandler(logging.Handler):
        """
        This handler does nothing. It's intended to be used to avoid the
        "No handlers could be found for logger XXX" one-off warning. This is
        important for library code, which may contain code to log events. If a
        user of the library does not configure logging, the one-off warning
        might be produced; to avoid this, the library developer simply needs to
        instantiate a NullHandler and add it to the top-level logger of the
        library module or package.
        """
        def handle(self, record):
            pass

        def emit(self, record):
            pass

        def createLock(self):
            self.lock = None


# ugly monkey patching to show full help rather than just usage
def _show(self, file=None):
    if file is None:
        file = click.get_text_stream('stderr')
    if self.ctx is not None:
        click.echo(self.ctx.get_help() + '\n', file=file)
    click.echo('Error: %s' % self.format_message(), file=file)
click.UsageError.show = _show


@click.group('dbsake',
             options_metavar='[options]',
             subcommand_metavar='<command>',
             invoke_without_command=True,
             context_settings=CONTEXT_SETTINGS)
@click.option("-d", "--debug", default=False, is_flag=True)
@click.option("-q", "--quiet", default=False, is_flag=True)
@click.version_option(dbsake_version, '-V', '--version')
@click.pass_context
def dbsake(ctx, debug, quiet):
    ctx.obj['debug'] = debug
    ctx.obj['quiet'] = quiet
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help(), file=sys.stderr)
    level = logging.INFO
    if quiet:
        # suppress all logging output
        logging.getLogger().addHandler(NullHandler())
    else:
        if debug:
            level = logging.DEBUG
        logging.basicConfig(format='%(message)s', level=level)


@dbsake.command()
@click.argument('command', required=False)
@click.pass_context
def help(ctx, command):
    """Show help for a command."""
    if command:
        cmd = dbsake.commands[command]
        ctx.info_name = command
        click.echo(cmd.get_help(ctx))
    else:
        click.echo(ctx.parent.get_help())
    sys.exit(0)


def handle_uncaught_exception(exc_type, exc_value, traceback):
    """Handle uncaught exceptions

    This method logs a stack trace for debugging purposes and directs the
    user to the dbsake issues tracker.
    """
    from traceback import format_exception
    issues_url = 'https://github.com/abg/dbsake/issues'
    click.echo("Uncaught exception!", nl=False, file=sys.stderr)
    emoji0 = " (\u256f\xb0\u25a1\xb0)\u256f \ufe35 \u253b\u2501\u253b"
    emoji1 = "\u252c\u2500\u252c\u30ce( \xba_ \xba\u30ce)"
    click.echo(emoji0.encode('utf-8'), file=sys.stderr)
    for line in format_exception(exc_type, exc_value, traceback):
        click.echo(line, nl=False, file=sys.stderr)
    click.echo(("It's okay. %s" % emoji1).encode('utf-8'), file=sys.stderr)
    click.echo("Consider filing a bug report at %s" % issues_url,
               file=sys.stderr)


def main(argv=None):
    """Main entry point

    This is our external interface and we dispatch to the underlying cli
    to enable various features (environment variables, etc.)
    """
    sys.excepthook = handle_uncaught_exception
    from . import cmd
    cmd.discover_commands()
    dbsake(args=argv, auto_envvar_prefix='DBSAKE', obj={})
    return 0
