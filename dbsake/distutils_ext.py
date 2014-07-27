"""
dbsake.distutils_ext
~~~~~~~~~~~~~~~~~~~~

Commands for distutils

Adds a bdist_dbsakesh script that creates an executable
zip archive to allow dbsake to run on any linux
distribution with python2.6+
"""
from __future__ import print_function

import errno
import os
import pkgutil
import stat
import sys
import zipfile

import distutils.core

SHELL_SCRIPT = """#!/bin/sh

python=$({ which python2.7 ||
           which python2.6 ||
           which python3; } 2>/dev/null)

if [ $? -ne 0 ]
then
    echo "No supported python command found." 2>&1
    python=$(which python 2>/dev/null)
    [ ?$ -eq 0 ] || \
        echo "However, found ${python} with version: $(python -V)" 2>&1
    echo "dbsake requires python2.6+, or python3+." 2>&1
    echo "Aborting." 2>&1
    exit 1
fi
${python} $0 $@
exit $?
"""


def is_excluded(name, excludes):
    """Check if a module name is in the list of excludes

    This checks if the module name starts with any string
    in excludes, so is a very naive check.
    """
    for prefix in excludes:
        if name.startswith(prefix):
            return True
    return False


def fetch_source(package, excludes=()):
    """Fetch the python source for the given package name

    This will import the named package and iterate over all its
    submodules to pull in the source code via PEP302 loaders.

    Each source file is yielded as ('relativepath', 'source string')
    tuples.

    NOTE: Only python source code is importing in this manner, so if
          a dependency has any non-python code (templates or other
          resources), or if the module intrinsically has no source
          code (i.e. compiled modules), this method is insufficient.
    """
    pkg = __import__(package)
    yield pkg.__name__ + '/__init__.py', pkgutil.get_loader(pkg).get_source(pkg.__name__)
    for importer, name, is_pkg in pkgutil.walk_packages(pkg.__path__,
                                                        pkg.__name__ + '.'):
        if is_excluded(name, excludes):
            continue
        loader = importer.find_module(name)
        source = loader.get_source(name)
        assert source is not None
        path = name.replace('.', '/')
        if is_pkg:
            path += '/__init__.py'
        else:
            path += '.py'
        yield path, source


class DBSakeBundler(distutils.core.Command):
    """Command to create a standalone dbsake shell script

    This creates an executable zip archive prefixed by a shell script to
    ensure dbsake fails gracefully in environments without a recent
    python executable.
    """

    description = 'create a standalone dbsake shell script'

    user_options = [
        ('dist-dir=', 'd',
         "directory to put final built distributions in"),
    ]

    # hardcoded, since there's not an easy way to look this up, afaik
    dependencies = [
        ('click', ['click.testing']),
        ('jinja2', ['jinja2.testsuite']),
        ('markupsafe', ['markupsafe._speedups', 'markupsafe.tests']),
    ]

    def initialize_options(self):
        self.dist_dir = None

    def finalize_options(self):
        if self.dist_dir is None:
            self.dist_dir = 'dist'

    def run(self):
        try:
            os.makedirs(self.dist_dir)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
        with open(os.path.join(self.dist_dir, 'dbsake.sh'), 'wb') as fileobj:
            os.fchmod(fileobj.fileno(),
                      stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR)
            fileobj.write(SHELL_SCRIPT.encode('utf-8'))
            compress_opt = zipfile.ZIP_DEFLATED
            with zipfile.ZipFile(file=fileobj,
                                 mode='w',
                                 compression=compress_opt) as archive:
                for dirpath, _, filenames in os.walk('dbsake'):
                    for name in filenames:
                        if (not name.endswith('.py') and
                                os.path.basename(dirpath) != 'templates'):
                            continue
                        path = os.path.join(dirpath, name)
                        if name != '__main__.py':
                            arcname = path
                        else:
                            arcname = name
                        archive.write(path, arcname)

                for depname, excludes in self.dependencies:
                    for name, source in fetch_source(depname, excludes):
                        archive.writestr(name, source)
        print("Generated %s" % fileobj.name, file=sys.stderr)
