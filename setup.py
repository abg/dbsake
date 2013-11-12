from setuptools import setup, find_packages

version = '1.0'

setup(
    name='dbsake',
    version=version,
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
