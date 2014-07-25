"""
dbsake.cli.cmd.mycnf
~~~~~~~~~~~~~~~~~~~~

MySQL option file utilitie
"""
from __future__ import unicode_literals

import sys

import click

from dbsake.cli import dbsake


@dbsake.command(name='upgrade-mycnf')
@click.option('-c', '--config',
              type=click.Path(dir_okay=False, resolve_path=True),
              default='/etc/my.cnf',
              help="my.cnf file to parse")
@click.option('-t', '--target',
              type=click.Choice(['5.1', '5.5', '5.6', '5.7']),
              default='5.5',
              help="MySQL version to target")
@click.option('-p', '--patch', is_flag=True,
              help="Output unified diff rather than full config")
def upgrade_mycnf(config, target, patch):
    """Upgrade a MySQL option file"""
    from dbsake.core.mysql import mycnf

    result = mycnf.upgrade(config, target, patch)
    click.echo(result)
    sys.exit(0)
