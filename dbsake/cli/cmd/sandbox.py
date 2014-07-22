"""
dbsake.cmd.sandbox
~~~~~~~~~~~~~~~~~

Command interface to create isolated MySQL "sandbox" instances
"""
from __future__ import unicode_literals

import sys

import click

from dbsake.cli import dbsake


@dbsake.command('mysql-sandbox')
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
@click.option('-D', '--data-source',
              metavar='<source>',
              type=click.Path(resolve_path=True, exists=True),
              help="path to file to populate sandbox")
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
@click.option('-p', '--password',
              default=False,
              is_flag=True,
              help="prompt for password to create root@localhost with")
@click.option('-x', '--innobackupex-options',
              metavar='<options>',
              help="additional options to run innobackupex --apply-logs",
              default='')
@click.pass_context
def sandbox_cli(ctx,
                sandbox_directory,
                mysql_distribution,
                data_source,
                include_tables,
                exclude_tables,
                cache_policy,
                skip_libcheck,
                skip_gpgcheck,
                force,
                password,
                innobackupex_options):
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

    try:
        sandbox.create(sandbox_directory=sandbox_directory,
                       mysql_distribution=mysql_distribution,
                       data_source=data_source,
                       include_tables=include_tables,
                       exclude_tables=exclude_tables,
                       cache_policy=cache_policy,
                       skip_libcheck=skip_libcheck,
                       skip_gpgcheck=skip_gpgcheck,
                       force=force,
                       password=password,
                       innobackupex_options=innobackupex_options)
    except sandbox.SandboxError as exc:
        ctx.fail("%s" % exc)
