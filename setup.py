#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pkgutil


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import dbsake


def find_packages(path, prefix):
    walk = pkgutil.walk_packages(path, prefix + '.')
    return [prefix] + [name for _, name, ispkg in walk if ispkg]


requirements = open('requirements.txt').read().split()
test_requirements = open('test_requirements.txt').read().split()
readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')


setup(
    name='dbsake',
    version=dbsake.__version__,
    description='db admin\'s (s)wiss (a)rmy (k)nif(e) for MySQL',
    long_description=readme + '\n\n' + history,
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
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    entry_points={
        'console_scripts': [
            'dbsake = dbsake.cli:main',
        ]
    },
)
