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
              type=click.Choice(['stream', 'directory']),
              help="Select the output format (directory, stream)")
@click.option('-C', '--directory',
              default='.',
              metavar='<path>',
              type=click.Path(resolve_path=True),
              help="Specify output directory when --format=directory")
@click.option('-i', '--input-file',
              metavar='<path>',
              type=click.File(mode='rb', lazy=False),
              default='-',
              help="Specify input file to process instead of stdin")
@click.option('-z', '--compress-command',
              metavar='<name>',
              default='gzip -1',
              help="Specify compression command when --format=directory")
@click.option('-t', '--table',
              metavar='<glob>',
              multiple=True,
              help="Only output tables matching the given glob pattern")
@click.option('-T', '--exclude-table',
              metavar='<glob>',
              multiple=True,
              help="Excludes tables matching the given glob pattern")
@click.option('--defer-indexes',
              is_flag=True,
              help="Add secondary indexes after loading table data")
@click.option('--defer-foreign-keys',
              is_flag=True,
              help="Add foreign key constraints after loading table data")
@click.option('--write-binlog/--disable-binlog',
              default=True,
              help="Include SQL_LOG_BIN = 0 in output to disable binlog")
@click.option('--table-data/--skip-table-data',
              default=True,
              help="Include/skip writing table data to output")
@click.option('--master-data/--no-master-data',
              default=None,
              help="Uncomment/comment CHANGE MASTER in input, if present")
@click.option('-f', '--force', is_flag=True,
              help="Force various behaviors in this command")
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
    """Filter and transform mysqldump output.

    sieve can extract single tables from a mysqldump file and perform useful
    transformations, such as adding indexes after the table data is loaded
    for InnoDB tables, where such indexes can be created much more efficiently
    than the default incremental rebuild that mysqldump performs.

    """
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
