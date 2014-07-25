"""
Test dbsake sandbox
"""
from __future__ import unicode_literals

from click.testing import CliRunner

from dbsake.cli.cmd.mycnf import upgrade_mycnf


def test_upgrade_mycnf_basic():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(upgrade_mycnf, ['--patch'],
                               auto_envvar_prefix='DBSAKE', obj={})
    assert result.exit_code == 0
