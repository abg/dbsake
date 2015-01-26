"""
Test dbsake.pycompat
"""
from __future__ import unicode_literals

import errno
import os
import shutil
import stat
import tempfile

import pytest

from dbsake import pycompat


def test_pycompat():
    pass


@pytest.yield_fixture
def base():
    tmpdir = tempfile.mkdtemp()
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir)


def test_makedir(base):
    path = os.path.join(base, 'dir1', 'dir2', 'dir3', '')
    pycompat.makedirs(path)
    path = os.path.join(base, 'dir1', 'dir2', 'dir3', 'dir4')
    pycompat.makedirs(path)

    # Try paths with a '.' in them
    with pytest.raises(OSError):
        pycompat.makedirs(os.curdir)

    path = os.path.join(base, 'dir1', 'dir2', 'dir3', 'dir4', 'dir5',
                        os.curdir)
    pycompat.makedirs(path)
    path = os.path.join(base, 'dir1', os.curdir, 'dir2', 'dir3', 'dir4',
                        'dir5', 'dir6')
    pycompat.makedirs(path)


def test_exist_ok_existing_directory(base):
    path = os.path.join(base, 'dir1')
    mode = 0o777
    old_mask = os.umask(0o022)
    pycompat.makedirs(path, mode)
    with pytest.raises(OSError):
        pycompat.makedirs(path, mode)
        pycompat.makedirs(path, mode, exist_ok=False)
    pycompat.makedirs(path, 0o776, exist_ok=True)
    pycompat.makedirs(path, mode=mode, exist_ok=True)
    os.umask(old_mask)


def test_exist_ok_s_isgid_directory(base):
    path = os.path.join(base, 'dir1')
    S_ISGID = stat.S_ISGID
    mode = 0o777
    old_mask = os.umask(0o022)
    try:
        existing_testfn_mode = stat.S_IMODE(os.lstat(base).st_mode)
        try:
            os.chmod(base, existing_testfn_mode | S_ISGID)
        except OSError as exc:
            if exc.errno == errno.EPERM:
                pytest.skip('Cannot set S_ISGID for dir.')
            else:
                raise

        if (os.lstat(base).st_mode & S_ISGID != S_ISGID):
            pytest.skip('No support for S_ISGID dir mode.')
        # The os should apply S_ISGID from the parent dir for us, but
        # this test need not depend on that behavior.  Be explicit.
        pycompat.makedirs(path, mode | S_ISGID)
        # http://bugs.python.org/issue14992
        # Should not fail when the bit is already set.
        pycompat.makedirs(path, mode, exist_ok=True)
        # remove the bit.
        os.chmod(path, stat.S_IMODE(os.lstat(path).st_mode) & ~S_ISGID)
        # May work even when the bit is not already set when demanded.
        pycompat.makedirs(path, mode | S_ISGID, exist_ok=True)
    finally:
        os.umask(old_mask)


def test_exist_ok_existing_regular_file(base):
    base = base
    path = os.path.join(base, 'dir1')
    f = open(path, 'w')
    f.write('abc')
    f.close()
    with pytest.raises(OSError):
        pycompat.makedirs(path)
        pycompat.makedirs(path, exist_ok=False)
        pycompat.makedirs(path, exist_ok=True)
    os.remove(path)


def test_chown(base):
    # cleaned-up automatically by TestShutil.tearDown method
    dirname = tempfile.mkdtemp(dir=base)
    filename = tempfile.mktemp(dir=dirname)
    with open(filename, 'wb') as fileobj:
        fileobj.write(b'testing chown function')

    with pytest.raises(ValueError):
        pycompat.chown(filename)

    with pytest.raises(LookupError):
        pycompat.chown(filename, user='non-exising username')

    with pytest.raises(LookupError):
        pycompat.chown(filename, group='non-exising groupname')

    if pycompat.PY3:
        with pytest.raises(TypeError):
            pycompat.chown(filename, b'spam')

    with pytest.raises(TypeError):
        pycompat.chown(filename, 3.14)

    uid = os.getuid()
    gid = os.getgid()

    def check_chown(path, uid=None, gid=None):
        s = os.stat(filename)
        if uid is not None:
            assert uid == s.st_uid
        if gid is not None:
            assert gid == s.st_gid

    pycompat.chown(filename, uid, gid)
    check_chown(filename, uid, gid)
    pycompat.chown(filename, uid)
    check_chown(filename, uid)
    pycompat.chown(filename, user=uid)
    check_chown(filename, uid)
    pycompat.chown(filename, group=gid)
    check_chown(filename, gid=gid)

    pycompat.chown(dirname, uid, gid)
    check_chown(dirname, uid, gid)
    pycompat.chown(dirname, uid)
    check_chown(dirname, uid)
    pycompat.chown(dirname, user=uid)
    check_chown(dirname, uid)
    pycompat.chown(dirname, group=gid)
    check_chown(dirname, gid=gid)

    import grp
    import pwd

    user = pwd.getpwuid(uid)[0]
    group = grp.getgrgid(gid)[0]
    pycompat.chown(filename, user, group)
    check_chown(filename, uid, gid)
    pycompat.chown(dirname, user, group)
    check_chown(dirname, uid, gid)


def test_disk_usage(base):
    usage = pycompat.disk_usage(os.getcwd())
    assert usage.total > 0
    assert usage.used > 0
    assert usage.free >= 0
    assert usage.total >= usage.used
    assert usage.total > usage.free


def test_relpath(base):
    assert pycompat.relpath("/foo/bar/baz", "/") == "foo/bar/baz"
    assert pycompat.relpath("/opt/sandboxes/mysql-5.6/data/mysql",
                            "/opt/sandboxes/mysql-5.6") == "data/mysql"

    with pytest.raises(ValueError):
        pycompat.relpath('')
