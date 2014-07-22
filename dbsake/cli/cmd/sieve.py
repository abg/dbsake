"""
dbsake.cmd.sieve
~~~~~~~~~~~~~~~~

Advanced filtering of mysqldump backup files
"""
from __future__ import unicode_literals

import errno
import signal
import sys

import click

from dbsake.cli import dbsake


@dbsake.command('sieve')
@click.option('-F', '--format', 'output_format',
              metavar='<name>',
              default='stream',
              type=click.Choice(['stream', 'directory']))
@click.option('-C', '--directory',
              default='.',
              metavar='<output directory>',
              type=click.Path(resolve_path=True))
@click.option('-i', '--input-file',
              metavar='<path>',
              type=click.File(mode='rb', lazy=False),
              default='-')
@click.option('-z', '--compress-command',
              metavar='<command>',
              default='gzip -1')
@click.option('-t', '--table', metavar='<glob pattern>', multiple=True)
@click.option('-T', '--exclude-table', metavar='<glob pattern>', multiple=True)
@click.option('--defer-indexes', is_flag=True)
@click.option('--defer-foreign-keys', is_flag=True)
@click.option('--write-binlog/--disable-binlog', default=True)
@click.option('--table-data/--skip-table-data', default=True)
@click.option('--master-data/--no-master-data', default=None)
@click.option('-f', '--force', is_flag=True)
@click.pass_context
def sieve_cli(ctx,
              output_format,
              directory,
              input_file,
              compress_command,
              table,
              exclude_table,
              defer_indexes,
              defer_foreign_keys,
              write_binlog,
              table_data,
              master_data,
              force):
    """Filter a mysqldump plaintext SQL stream"""
    from dbsake.core.mysql import sieve

    if output_format == 'stream' and sys.stdout.isatty() and not force:
        ctx.fail("stdout appears to be a terminal and --format=stream. "
                 "Aborting.")

    if defer_indexes and not table_data:
        click.echo("Disabling index deferment since --no-data requested",
                   file=sys.stderr)
        defer_indexes = False
        defer_foreign_keys = False

    options = sieve.Options(output_format=output_format,
                            table_data=table_data,
                            master_data=master_data,
                            defer_indexes=defer_indexes,
                            defer_foreign_keys=defer_foreign_keys,
                            table=table,
                            exclude_table=exclude_table,
                            write_binlog=write_binlog,
                            directory=directory,
                            compress_command=compress_command,
                            input_stream=input_file,
                            output_stream=click.get_binary_stream('stdout'))

    with input_file:
        try:
            sieve.sieve(options)
        except IOError as exc:
            if exc.errno != errno.EPIPE:
                raise  # generate a traceback, in case this is a bug
            else:
                # note broken pipe in debug mode
                if ctx.obj['debug']:
                    click.echo("Broken pipe (errno: %d)" % exc.errno,
                               file=sys.stderr)
                # exit with SIGPIPE to indicate only partial output
                sys.exit(128 + signal.SIGPIPE)
        except sieve.Error as exc:
            click.fail(exc)
