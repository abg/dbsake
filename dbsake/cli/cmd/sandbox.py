"""
dbsake.cmd.sandbox
~~~~~~~~~~~~~~~~~

Command interface to create isolated MySQL "sandbox" instances
"""
from __future__ import unicode_literals

import os
import sys

import click

from dbsake.cli import dbsake


@dbsake.command('sandbox', options_metavar='[options]')
@click.option('-d', '--sandbox-directory',
              metavar='<path>',
              type=click.Path(file_okay=False,
                              writable=True,
                              resolve_path=True),
              help="path where sandbox will be installed")
@click.option('-m', '--mysql-distribution',
              metavar='<dist>',
              default='system',
              help="mysql distribution to install")
@click.option('-D', '--datadir',
              metavar='<path>',
              type=click.Path(resolve_path=True, file_okay=False),
              help="Path to datadir for sandbox")
@click.option('-s', '--data-source',
              metavar='<source>',
              type=click.Path(resolve_path=True, exists=True, dir_okay=False),
              help="path to file to populate sandbox")
@click.option('--progress/--no-progress', 'report_progress',
              default=sys.stderr.isatty(),
              help='Enable/disable progressbars when unpacking archives.')
@click.option('include_tables', '-t', '--table',
              metavar='<glob-pattern>',
              multiple=True,
              help="db.table glob pattern to include from --data-source")
@click.option('exclude_tables', '-T', '--exclude-table',
              metavar='<glob-pattern>',
              multiple=True,
              help="db.table glob pattern to exclude from --data-source")
@click.option('-c', '--cache-policy',
              metavar='<policy>',
              default='always',
              type=click.Choice(['always', 'never', 'refresh', 'local']),
              help="cache policy to apply when downloading mysql distribution")
@click.option('--skip-libcheck', default=False, is_flag=True,
              help="skip check for required system libraries")
@click.option('--skip-gpgcheck', default=False, is_flag=True,
              help="skip gpg verification of download mysql distributions")
@click.option('--force', default=False, is_flag=True,
              help="overwrite existing sandbox directory")
@click.option('-u', '--mysql-user',
              metavar='<user>',
              default='root',
              help="MySQL user to add to the sandbox instance")
@click.option('-p', '--password',
              default=False,
              is_flag=True,
              help="prompt for password to create root@localhost with")
@click.option('-x', '--innobackupex-options',
              metavar='<options>',
              help="additional options to run innobackupex --apply-logs",
              default='')
def sandbox_cli(sandbox_directory,
                mysql_distribution,
                datadir,
                data_source,
                include_tables,
                exclude_tables,
                cache_policy,
                skip_libcheck,
                skip_gpgcheck,
                force,
                mysql_user,
                password,
                innobackupex_options,
                report_progress):
    """Create a sandboxed MySQL instance.

    This command installs a new MySQL instance under the specified sandbox
    directory, or under ~/sandboxes/sandbox_<datetime> if none is specified.
    """
    from dbsake.core.mysql import sandbox

    if password:
        if not sys.stdin.isatty():
            options = dict(text='',
                           prompt_suffix='')
        else:
            options = dict(text='Password',
                           confirmation_prompt=True,
                           hide_input=True)
        password = click.prompt(**options)

    # only add mysql.* if at least some inclusion pattern
    # is specified, or *only* mysql.* tables will be
    # extracted rather than everything by default.
    if include_tables:
        include_tables += ('mysql.*',)

    try:
        sandbox.create(sandbox_directory=sandbox_directory,
                       mysql_distribution=mysql_distribution,
                       datadir=datadir,
                       data_source=data_source,
                       include_tables=include_tables,
                       exclude_tables=exclude_tables,
                       cache_policy=cache_policy,
                       skip_libcheck=skip_libcheck,
                       skip_gpgcheck=skip_gpgcheck,
                       force=force,
                       mysql_user=mysql_user,
                       password=password,
                       innobackupex_options=innobackupex_options,
                       report_progress=report_progress)
    except sandbox.SandboxError as exc:
        click.echo("%s" % exc, file=sys.stderr)
        sys.exit(os.EX_SOFTWARE)
