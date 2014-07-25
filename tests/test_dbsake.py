"""
Test dbsake cli
"""
from __future__ import unicode_literals

from click.testing import CliRunner

import dbsake
from dbsake import cli


def test_help():
    runner = CliRunner()
    result = runner.invoke(cli.dbsake, ['help'], obj={})
    assert result.exit_code == 0


def test_quiet_option():
    runner = CliRunner()
    result = runner.invoke(cli.dbsake, ["--quiet", "help"], obj={})
    assert result.exit_code == 0


def test_debug_option():
    runner = CliRunner()
    result = runner.invoke(cli.dbsake, ["--debug", "help"], obj={})
    assert result.exit_code == 0


def test_dbsake_version():
    runner = CliRunner()
    result = runner.invoke(cli.dbsake, ["--version"], obj={})
    assert result.exit_code == 0
    assert result.output == 'dbsake, version %s\n' % dbsake.__version__
