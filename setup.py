from setuptools import setup, find_packages

from dbsake import __version__

setup(
    name='dbsake',
    version=__version__,
    description="",
    long_description="",
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='',
    author_email='',
    url='',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    entry_points="""
    [console_scripts]
    dbsake = dbsake:main
    """,
)
