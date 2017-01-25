"""
dbsake.cli.cmd.mycnf
~~~~~~~~~~~~~~~~~~~~

MySQL option file utilitie
"""
import os
import sys

import click

from dbsake.cli import dbsake


@dbsake.command('upgrade-mycnf', options_metavar='[options]')
@click.option('-c', '--config',
              type=click.Path(dir_okay=False, resolve_path=False),
              default='/etc/my.cnf',
              metavar='<path>',
              help="my.cnf file to parse")
@click.option('-t', '--target',
              type=click.Choice(['5.1', '5.5', '5.6', '5.7']),
              default='5.5',
              show_default=True,
              help="MySQL version to target")
@click.option('-p', '--patch', is_flag=True,
              help="Output unified diff rather than full config")
def upgrade_mycnf(config, target, patch):
    """Upgrade a MySQL option file"""
    from dbsake.core.mysql import mycnf

    config = os.path.expanduser(config)

    if not os.path.exists(config):
        click.echo("Unreadable config '%s'" % (config,), err=True)
        sys.exit(os.EX_CONFIG)

    result = mycnf.upgrade(config, target, patch)
    click.echo(result)
    sys.exit(0)
