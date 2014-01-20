"""
dbsake.mysql.sandbox.datasource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Support for importing data sources

"""

import fnmatch
import os
import tarfile

from dbsake.mysql.frm import tablename

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
            if fnmatch(name, pattern):
                return False # don't filter
        return True # not in an include pattern

    return _filter

def _is_tarball(path):
    # check for either .tar or .tar.[ext]
    for _ in xrange(2):
        path, ext = os.path.splitext(path)
        if ext == 'tar':
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
        info("  Preloading sandbox data from %s", options.datasource)
        deploy_tarball(options.datasource,
                       os.path.join(options.basedir, 'data'))
    elif _is_sqldump(sandbox_options.datasource):
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


def deploy_tarball(datasource, datadir):
    with tarfile.open(datasource, 'r|*') as tar:
        for tarinfo in tar:
            '''
            Here we need to keep several files by default before we apply table filters

            ibdata* ib_logfile* -> critical for innodb, always keep
            backup-my.cnf, xtrabackup* -> critical for xtrabackup, always keep

            '''
            name = os.path.normpath(tarinfo.name).replace('/', '.')
            name = tablename.decode(name)
            if _should_filter(name): continue
            tar.extract(tarinfo, datadir)

