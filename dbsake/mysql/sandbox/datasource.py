"""
dbsake.mysql.sandbox.datasource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Support for importing data sources

"""
from __future__ import print_function

import fnmatch
import logging
import os
import sys
import tarfile

from dbsake.mysql.frm import tablename

from . import common
from . import util

logger = logging.getLogger()
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

def is_tarball(path):
    try:
        return tarfile.is_tarfile(path)
    except IOError:
        return False

def _is_sqldump(path):
    for _ in xrange(2):
        path, ext = os.path.splitext(path)
        if ext == 'sql':
            return True
    return False

def prepare_datadir(datadir):
    from dbsake.util.path import which

    innobackupex = which('innobackupex')
    if not innobackupex:
        raise common.SandboxError("innobackupex not found in path. Unable to prepare backup data.")

    from dbsake.thirdparty import sarge

    xb_log = os.path.join(datadir, 'innobackupex.log')
    cmd = sarge.shell_format('{0} --apply-log . > innobackupex.log 2>&1',
                             innobackupex)
    info("    - Running: %s", cmd)
    info("    - (cwd: %s)", datadir)
    result = sarge.run(cmd, cwd=datadir)

    if result.returncode != 0:
        info("    ! innobackupex --apply-log failed. See details in %s", xb_log)
        raise common.SandboxError("Data preloading failed")
    else:
        info("    - innobackupex --apply-log succeeded. datadir is ready.")

def preload(options):
    if not options.datasource:
        return
    elif is_tarball(options.datasource):
        # build table filter from tables/exclude_tables
        # So here we want to map database.table to database/table
        # filtering the database and tablename through the mysql
        # tablename encoders
        _filter = table_filter(options.tables, options.exclude_tables)
        info("  Preloading sandbox data from %s", options.datasource)
        datadir = os.path.join(options.basedir, 'data')
        deploy_tarball(options.datasource, datadir, table_filter=_filter)
        ib_logfile = os.path.join(datadir, 'ib_logfile0')
        xb_logfile = os.path.join(datadir, 'xtrabackup_logfile')
        if not os.path.exists(ib_logfile) and os.path.exists(xb_logfile):
            info("    - Sandbox data appears to be an unprepared xtrabackup image")
            prepare_datadir(datadir)
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
    show_progress = os.isatty(sys.stderr.fileno())
    with util.StreamProxy(open(datasource, 'rb')) as proxy:
        if show_progress:
            proxy.add(util.progressbar(max=os.fstat(proxy.fileno()).st_size))
        tar = tarfile.open(None, mode='r|*', fileobj=proxy, ignore_zeros=True)
        for tarinfo in tar:
            if not tarinfo.isreg(): continue
            tarinfo.name = os.path.normpath(tarinfo.name)
            if _is_required(tarinfo.name):
                if logger.isEnabledFor(logging.DEBUG) and show_progress:
                    print(" "*80, file=sys.stderr, end="\r")
                debug("    # Extracting required file: %s", tarinfo.name)
                tar.extract(tarinfo, datadir)
                continue
            # otherwise treat it like a table
            name, _ = os.path.splitext(tarinfo.name) # remove extension
            # remove partition portion
            name = name.partition('#P')[0]
            name = name.replace('/', '.')
            name = tablename.decode(name)
            if table_filter(name):
                if logger.isEnabledFor(logging.DEBUG):
                    print(" "*80, file=sys.stderr, end="\r")
                    debug("    # Excluding %s - excluded by table filters", tarinfo.name)
                continue
            if logger.isEnabledFor(logging.DEBUG):
                print(" "*80, file=sys.stderr, end="\r")
                debug("    # Extracting %s", tarinfo.name)
            tar.extract(tarinfo, datadir)
