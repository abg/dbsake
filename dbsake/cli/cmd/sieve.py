"""
dbsake.cmd.sieve
~~~~~~~~~~~~~~~~

Advanced filtering of mysqldump backup files
"""
import errno
import signal
import sys

import click

from dbsake.cli import dbsake


@dbsake.command('sieve', options_metavar='[options]')
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
@click.option('--write-binlog/--no-write-binlog',
              default=True,
              help="Include SQL_LOG_BIN = 0 in output to disable binlog")
@click.option('--table-schema/--no-table-schema',
              default=True,
              help="Include/exclude table schema from output.")
@click.option('--table-data/--no-table-data',
              default=True,
              help="Include/exclude table data from output")
@click.option('--routines/--no-routines',
              default=None,
              help="Include / exclude database routines from output")
@click.option('--events/--no-events',
              default=None,
              help="Include / exclude database events from output")
@click.option('--triggers/--no-triggers',
              default=None,
              help="Include/exclude table triggers from output")
@click.option('--master-data/--no-master-data',
              default=None,
              help="Uncomment/comment CHANGE MASTER in input, if present")
@click.option('-O', '--to-stdout', is_flag=True,
              help="Force output on stdout, even to a terminal.")
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
              table_schema,
              table_data,
              routines,
              events,
              triggers,
              master_data,
              to_stdout):
    """Filter and transform mysqldump output.

    sieve can extract single tables from a mysqldump file and perform useful
    transformations, such as adding indexes after the table data is loaded
    for InnoDB tables, where such indexes can be created much more efficiently
    than the default incremental rebuild that mysqldump performs.

    Example:

        $ dbsake sieve --no-table-data < sakila.sql.gz > sakila_schema.sql
        $ dbsake sieve --format=directory -i sakila.sql.gz -C extracted_sql/
    """
    from dbsake.core.mysql import sieve

    if hasattr(input_file, 'detach'):
        input_file = input_file.detach()

    if output_format == 'stream' and sys.stdout.isatty() and not to_stdout:
        ctx.fail("stdout appears to be a terminal and --format=stream. "
                 "Use -O/--to-stdout to force output or redirect to a file. "
                 "Aborting.")

    if defer_indexes and not table_data:
        click.echo("Disabling index deferment since --no-data requested",
                   file=sys.stderr)
        defer_indexes = False
        defer_foreign_keys = False

    options = sieve.Options(output_format=output_format,
                            table_schema=table_schema,
                            table_data=table_data,
                            routines=routines,
                            events=events,
                            triggers=triggers,
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

    try:
        stats = sieve.sieve(options)
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
        click.echo(exc, file=sys.stderr)
        sys.exit(1)
    else:
        click.echo(("Processed %s. "
                    "Output: %d database(s) %d table(s) and %d view(s)") %
                   (options.input_stream.name,
                    stats['createdatabase'] or 1,
                    stats['tablestructure'],
                    stats['view']), file=sys.stderr)
        sys.exit(0)
