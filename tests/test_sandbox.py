"""
Test dbsake sandbox
"""
import os
import tarfile

import pytest

from click.testing import CliRunner

from dbsake.cli.cmd.sandbox import sandbox_cli


def test_sandbox_system():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(sandbox_cli, ['-d', 'mysql_system'], obj={})
    assert result.exit_code == 0


@pytest.mark.skipif(os.environ.get('TRAVIS', 'false') == 'true',
                    reason="Skipping sandbox CDN tests on travis-ci")
def test_sandbox_50():
    runner = CliRunner()
    with runner.isolated_filesystem():
        sbdir = os.path.abspath('test_sandbox')
        result = runner.invoke(sandbox_cli,
                               ['-d', sbdir, '-m', '5.0.95'],
                               auto_envvar_prefix='DBSAKE', obj={})
        assert result.exit_code == 0
        result = runner.invoke(sandbox_cli,
                               ['--force',
                                '-d', sbdir,
                                '-m', '5.0.95'],
                               auto_envvar_prefix='DBSAKE', obj={})
        assert result.exit_code == 0
        tar = tarfile.open("backup.tar.gz", "w:gz")
        cwd = os.getcwd()
        os.chdir(os.path.join(sbdir, 'data'))
        tar.add('.')
        tar.close()
        os.chdir(cwd)
        result = runner.invoke(sandbox_cli,
                               ['--force',
                                '-d', sbdir,
                                '-m', '5.0.95',
                                '-s', 'backup.tar.gz',
                                '-t', 'mysql.user'],
                               auto_envvar_prefix='DBSAKE', obj={})
        assert result.exit_code == 0

'''
def test_sandbox_51():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(sandbox_cli,
                               ['-d', 'mysql_system', '-m', '5.1.72'],
                               auto_envvar_prefix='DBSAKE', obj={})
    assert_equals(result.exit_code, 0)

def test_sandbox_55():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(sandbox_cli,
                               ['-d', 'mysql_system', '-m', '5.5.38'],
                               auto_envvar_prefix='DBSAKE', obj={})
    assert_equals(result.exit_code, 0)

def test_sandbox_56():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(sandbox_cli,
                               ['-d', 'mysql_system', '-m', '5.6.19'],
                               auto_envvar_prefix='DBSAKE', obj={})
    assert result.exit_code == 0

def test_sandbox_57():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(sandbox_cli,
                               ['-d', 'mysql_system', '-m', '5.7.4-m14'],
                               auto_envvar_prefix='DBSAKE', obj={})
    assert_equals(result.exit_code, 0)
'''
