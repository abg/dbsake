"""
Test dbsake cli
"""
from __future__ import unicode_literals

import os

from click.testing import CliRunner

from dbsake.cli.cmd.sieve import sieve_cli


def test_sieve_stream():
    runner = CliRunner()
    path = os.path.join(os.path.dirname(__file__), 'sakila.sql.gz')
    args = [
        '--defer-indexes',
        '--table=sakila.actor*',
        '--exclude-table=sakila.actor_info',
        '--no-master-data',
        '--input-file=' + path
    ]
    result = runner.invoke(sieve_cli, args, obj={})
    assert result.exit_code == 0


def test_sieve_directory():
    runner = CliRunner()
    sakila_path = os.path.join(os.path.dirname(__file__), 'sakila.sql.gz')
    args = ['--format=directory', '--input-file=' + sakila_path]
    with runner.isolated_filesystem():
        result = runner.invoke(sieve_cli, args, obj={})
        assert result.exit_code == 0


def test_sieve_w_mariadb10_gtid():
    runner = CliRunner()
    path = os.path.join(os.path.dirname(__file__),
                        'mariadb_gtid_master_data.sql.gz')

    args = ['--format=stream', '--input-file=' + path, '-O']
    result = runner.invoke(sieve_cli, args, obj={})
    assert result.exit_code == 0
