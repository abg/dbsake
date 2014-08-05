"""
Test dbsake sandbox
"""
from __future__ import unicode_literals

import os

from click.testing import CliRunner

from dbsake.cli.cmd.mycnf import upgrade_mycnf


def test_upgrade_mycnf_basic():
    runner = CliRunner()
    config_path = os.path.join(os.path.dirname(__file__), 'my.cnf')
    with runner.isolated_filesystem():
        result = runner.invoke(upgrade_mycnf,
                               ['--config=%s' % config_path, '--patch'],
                               auto_envvar_prefix='DBSAKE', obj={})
    assert result.exit_code == 0
