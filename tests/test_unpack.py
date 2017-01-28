"""
Test unpack command
"""
from __future__ import unicode_literals

import os
import shutil

from click.testing import CliRunner

import dbsake.cli
from dbsake.cli.cmd.unpack import _unpack

from dbsake.util import cmd


def test_help():
    runner = CliRunner()
    result = runner.invoke(dbsake.cli.dbsake, ['help', 'unpack'], obj={})
    assert result.exit_code == 0


def test_unpack_xb_compressed_file():
    runner = CliRunner()
    src = os.path.join(os.path.dirname(__file__), 'backup.xb.gz')
    with runner.isolated_filesystem():
        result = runner.invoke(_unpack, [src], obj={})
    assert result.exit_code == 0


def test_unpack_xb_compressed_pipe():
    runner = CliRunner()
    src = os.path.join(os.path.dirname(__file__), 'backup.xb.gz')
    with runner.isolated_filesystem():
        cat_cmd = cmd.shell_format("cat {0}", src)
        with cmd.piped_stdout(cat_cmd) as stdin:
            result = runner.invoke(_unpack, ["-"], obj={}, input=stdin)
    assert result.exit_code == 0


def test_unpack_xb_uncompressed_file():
    runner = CliRunner()
    src = os.path.join(os.path.dirname(__file__), 'backup.xb.gz')
    with runner.isolated_filesystem():
        cat_cmd = cmd.shell_format("zcat {0}", src)
        with cmd.piped_stdout(cat_cmd) as stdin:
            with open("backup.xb", "wb") as stdout:
                shutil.copyfileobj(stdin, stdout)
        result = runner.invoke(_unpack, [src], obj={})
    assert result.exit_code == 0


def test_unpack_xb_uncompressed_pipe():
    runner = CliRunner()
    src = os.path.join(os.path.dirname(__file__), 'backup.xb.gz')
    with runner.isolated_filesystem():
        cat_cmd = cmd.shell_format("zcat {0}", src)
        with cmd.piped_stdout(cat_cmd) as stdin:
            result = runner.invoke(_unpack, ["-"], obj={}, input=stdin)
    assert result.exit_code == 0
