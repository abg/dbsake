"""
dbsake.mysql.sandbox.datasource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Support for importing data sources

"""

import fnmatch
import logging
import os
import tarfile

from dbsake.mysql.frm import tablename

info = logging.info
debug = logging.debug

# yeah, don't convert patterns at all that's painful
# instead we'll decode each filename we run across 
# and then match it against the pattern instead
def table_filter(include, exclude):
    if not include:
        include = ('*',)

    def _filter(name):
        for pattern in exclude:
            if fnmatch.fnmatch(name, pattern):
                return True # should exclude

        for pattern in include:
            if fnmatch.fnmatch(name, pattern):
                return False # don't filter
        return True # not in an include pattern

    return _filter

def _is_tarball(path):
    # check for either .tar or .tar.[ext]
    for _ in xrange(2):
        path, ext = os.path.splitext(path)
        if ext == '.tar':
            return True
    return False

def _is_sqldump(path):
    for _ in xrange(2):
        path, ext = os.path.splitext(path)
        if ext == 'sql':
            return True
    return False

def preload(options):
    if not options.datasource:
        return
    elif _is_tarball(options.datasource):
        # build table filter from tables/exclude_tables
        # So here we want to map database.table to database/table
        # filtering the database and tablename through the mysql
        # tablename encoders
        _filter = table_filter(options.tables, options.exclude_tables)
        info("  Preloading sandbox data from %s", options.datasource)
        deploy_tarball(options.datasource,
                       os.path.join(options.basedir, 'data'),
                       table_filter=_filter)
    elif _is_sqldump(options.datasource):
        # nothing to do before the sandbox is started
        pass

def finalize(sandbox_options):
    if _is_tarball(datasource):
        # then we've successfully ran through bootstrap phase
        # remove the ib_logfile so we startup with the my.cnf values
        for name in glob(basedir + 'data/ib_logfile*'):
            os.unlink(name)
    elif _is_sqldump(datasource):
        pass
        # start sandbox
        # pipe data in through shell
        # ./sandbox start
        # ./sandbox shell <datafiles>
        # sarge.run(sandbox.start) || fail
        # try:
        #   with sarge.run(sanbox shell, async=True, stdin=PIPE, stderr|stdout=import.log):
        #       for each sql file:
        #           with open(sql_file, 'rb') as fileobj:
        #               shutil.copyfileobj(fileobj, stdin)
        # finally:
        #   sarge.run(sandbox.stop) || fail

required_file_patterns = [
    'ibdata*', # typical name for shared tablespace
    'ib_logfile[0-9]*', # innodb redo log names
    'backup-my.cnf', # used by xtrabackup
    'xtrabackup*', # various xtrabackup files requires
    'aria_log*',
]
def _is_required(path):
    for pattern in required_file_patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False

def deploy_tarball(datasource, datadir, table_filter):
    
    tar = tarfile.open(datasource, 'r|*')
    # python 2.6's tarfile does not support the context manager protocol
    # so try...finally is used here
    try:
        for tarinfo in tar:
            if not tarinfo.isreg(): continue
            tarinfo.name = os.path.normpath(tarinfo.name)
            if _is_required(tarinfo.name):
                info("    - Extracting required file: %s", tarinfo.name)
                tar.extract(tarinfo, datadir)
                continue
            # otherwise treat it like a table
            name, _ = os.path.splitext(tarinfo.name) # remove extension
            # remove partition portion
            name = name.partition('#P')[0]
            name = name.replace('/', '.')
            name = tablename.decode(name)
            if table_filter(name):
                info("    > Excluding %s - excluded by table filters", tarinfo.name)
                continue
            #info("    - Extracting %s", tarinfo.name)
            tar.extract(tarinfo, datadir)
    finally:
        tar.close()
