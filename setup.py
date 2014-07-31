#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import pkgutil


try:
    from setuptools import setup, Command
except ImportError:
    from distutils.core import setup, Command

import dbsake
from dbsake.distutils_ext import DBSakeBundler


class PyTest(Command):
    user_options = []
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import sys,subprocess
        errno = subprocess.call([sys.executable, 'runtests.py'])
        raise SystemExit(errno)


def find_packages(path, prefix):
    walk = pkgutil.walk_packages(path, prefix + '.')
    return [prefix] + [name for _, name, ispkg in walk if ispkg]


def load_requirements(path):
    result = []
    with codecs.open(path, 'r', encoding='utf-8') as fileobj:
        for line in fileobj:
            if line.startswith("#"):
                continue
            result.append(line.rstrip())
    return result


def load_readme():
    with open('README.rst') as fileobj:
        data = fileobj.read()
    with open('HISTORY.rst') as fileobj:
        data += "\n\n" + fileobj.read().replace('.. :changelog:', '')
    return data


requirements = load_requirements('requirements.txt')
test_requirements = load_requirements('test_requirements.txt')
readme = load_readme()

setup(
    name='dbsake',
    version=dbsake.__version__,
    description='db admin\'s (s)wiss (a)rmy (k)nif(e) for MySQL',
    long_description=readme,
    author='Andrew Garner',
    author_email='andrew.garner@rackspace.com',
    url='https://github.com/abg/dbsake',
    packages=find_packages(dbsake.__path__, dbsake.__name__),
    package_dir={'dbsake':
                 'dbsake'},
    include_package_data=True,
    install_requires=requirements,
    license="GPLv2",
    zip_safe=False,
    keywords='dbsake',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    cmdclass={
        'test': PyTest,
        'bundle_dbsake': DBSakeBundler,
    },
    tests_require=test_requirements,
    entry_points={
        'console_scripts': [
            'dbsake = dbsake.cli:main',
        ]
    },
)
