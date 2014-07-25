"""
Test dbsake cli
"""
from __future__ import unicode_literals

import os
import gzip

from click.testing import CliRunner

from dbsake.cli.cmd.sieve import sieve_cli


class _GzipFile(gzip.GzipFile):
    """Shim for GzipFile so instances can be used as context managers"""
    closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        self.closed = True


def test_sieve_stream():
    runner = CliRunner()
    path = os.path.join(os.path.dirname(__file__), 'sakila.sql.gz')
    args = [
        '--defer-indexes',
        '--table=sakila.actor*',
        '--exclude-table=sakila.actor_info',
        '--no-master-data',
    ]
    with _GzipFile(path, "rb") as fileobj:
        result = runner.invoke(sieve_cli, args, obj={}, input=fileobj)
    assert result.exit_code == 0


def test_sieve_directory():
    runner = CliRunner()
    sakila_path = os.path.join(os.path.dirname(__file__), 'sakila.sql.gz')
    args = ['--format=directory']
    with runner.isolated_filesystem():
        with _GzipFile(sakila_path, 'rb') as fileobj:
            result = runner.invoke(sieve_cli, args, obj={}, input=fileobj)
        assert result.exit_code == 0
