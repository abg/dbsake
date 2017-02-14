# -*- coding: utf-8 -*-
from __future__ import print_function

import codecs
import glob
import os

import pytest

from click.testing import CliRunner

from dbsake.cli.cmd.frm import frmdump

from dbsake.core.mysql.frm import tablename


FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures')


def clean_frm(data):
    return "\n".join([line for line in data.splitlines()
                     if line.strip() and not line.startswith("--")]) + "\n"


def load_frm_test_data():
    """Finds test .frm and expected sql results from the local test_data path

    This methods loops through each .frm find under ./test_data/ and
    yields a path to an .frm and that .frm's expected result.  This is
    used to test that the frmdump command's result matches our expectations
    """
    test_data = os.path.join(FIXTURE_PATH, "*.frm")
    for frm_path in glob.glob(test_data):
        yield os.path.splitext(os.path.basename(frm_path))[0]


@pytest.mark.parametrize("name", load_frm_test_data())
def test_frm_decode(name):
    runner = CliRunner()
    frm_path = os.path.join(FIXTURE_PATH, name + '.frm')
    sql_path = os.path.join(FIXTURE_PATH, name + '.sql')
    result = runner.invoke(frmdump, [frm_path], obj={})
    assert result.exit_code == 0
    derived_sql = clean_frm(result.output)
    with codecs.open(sql_path, 'r', 'utf-8') as fileobj:
        expected_sql = fileobj.read()
    assert derived_sql == expected_sql


def test_frmdump_recursive():
    runner = CliRunner()
    expected_frm_count = len([name for name in os.listdir(FIXTURE_PATH)
                              if name.endswith('.frm')])
    result = runner.invoke(frmdump, ['--recursive', FIXTURE_PATH], obj={})
    computed_frm_count = result.output.count('\nCREATE ')
    assert result.exit_code == 0
    assert computed_frm_count == expected_frm_count


def test_frm_tablename():
    sample = u'Настройки'
    expected_encoding = b'@T0@g0@x0@y0@w0@u0@p0@q0@o0'

    result = tablename.encode(sample)

    assert result == expected_encoding

    orig = tablename.decode(result)

    assert orig == sample
