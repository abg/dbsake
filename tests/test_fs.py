"""
Test dbsake sandbox
"""
from __future__ import unicode_literals

from click.testing import CliRunner

from dbsake.cli.cmd import fs as fs_cli

from dbsake.core import fs


def test_fincore_basic():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(fs_cli.fincore, [__file__], obj={})
    assert result.exit_code == 0


def test_fincore_invalid_path():
    # issue #72
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(fs_cli.fincore, ['does-not-exist'], obj={})
        # This should be an EISDIR error, but some exit
        # code should be returned - not an exception
        assert result.exit_code > 0


def test_uncache_basic():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(fs_cli.uncache, [__file__], obj={})
    assert result.exit_code == 0


def test_fincore_api():
    fs.fincore(__file__)


def test_uncache_api():
    fs.uncache(__file__)
