"""
Test dbsake.util.compression

"""
from __future__ import unicode_literals

from dbsake.util import compression


def test_progress_bar(capsys):
    p = compression.progress_bar(100)

    for _ in range(100):
        p(1)
    p(0) # <- indicate finished progress bar

    out, err = capsys.readouterr()

    assert out == ''

    assert err.endswith("\n")

    for i, line in enumerate(err.split("\r"), start=1):
        assert line is not None
        if i > 100:
            i = 100
            assert line.endswith("\n")
        assert line.startswith("%d.0%%" % i)


def test_rate_bar(capsys):
    p = compression.rate_bar()

    for _ in range(100):
        p(1)
    p(0) # <- indicate finished progress bar

    out, err = capsys.readouterr()

    assert out == ''

    assert err.endswith("\n")

    assert len(err.split("\r")) == 101 # 101 updates
