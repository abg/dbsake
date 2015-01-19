"""
dbsake.core.mysql.sandbox.datasource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Support for importing data sources

"""
from __future__ import print_function

import fnmatch
import logging
import os
import re
import sys
import tarfile
import time

from dbsake import pycompat
from dbsake.util import cmd
from dbsake.util import compression

from dbsake.core.mysql.frm import tablename

from . import common

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
                return True  # should exclude

        for pattern in include:
            if fnmatch.fnmatch(name, pattern):
                return False  # don't filter
        return True  # not in an include pattern

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


def prepare_datadir(datadir, options):
    innobackupex = pycompat.which('innobackupex')
    if not innobackupex:
        raise common.SandboxError("innobackupex not found in path. Aborting.")

    xb_log = os.path.join(datadir, 'innobackupex.log')
    xb_cmd = cmd.shell_format('{0} --apply-log {1!s} .',
                              innobackupex, options.innobackupex_options)
    info("    - Running: %s", xb_cmd)
    info("    - (cwd: %s)", datadir)
    with open(xb_log, 'wb') as fileobj:
        returncode = cmd.run(xb_cmd,
                             stdout=fileobj,
                             stderr=fileobj,
                             cwd=datadir)

    if returncode != 0:
        info("    ! innobackupex --apply-log failed. See details in %s",
             xb_log)
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
        start = time.time()
        _filter = table_filter(options.include_tables, options.exclude_tables)
        info("  Preloading sandbox data from %s", options.datasource)
        datadir = options.datadir
        deploy_tarball(options.datasource, datadir, table_filter=_filter)
        ib_logfile = os.path.join(datadir, 'ib_logfile0')
        xb_logfile = os.path.join(datadir, 'xtrabackup_logfile')
        if not os.path.exists(ib_logfile) and os.path.exists(xb_logfile):
            info("    - Sandbox data appears to be unprepared xtrabackup data")
            prepare_datadir(datadir, options)
        info("    * Data extracted in %.2f seconds", time.time() - start)
    else:
        raise common.SandboxError("Unsupported data source: %s" %
                                  options.datasource)


#: files required for the sandbox - and never filtered
is_required = re.compile('(ibdata.*|ib_logfile[0-9]+|backup-my.cnf|'
                         'xtrabackup.*|aria_log.*|'
                         'mysql/slave_.*|mysql/innodb_.*)$')


def deploy_tarball(datasource, datadir, table_filter):
    show_progress = sys.stderr.isatty()
    if show_progress:
        decompress = compression.decompressed_w_progress
    else:
        decompress = compression.decompressed

    with decompress(datasource) as fileobj:
        tar = tarfile.open(mode='r|', fileobj=fileobj, ignore_zeros=True)
        for tarinfo in tar:
            if not tarinfo.isreg():
                continue
            tarinfo.name = os.path.normpath(tarinfo.name)
            if is_required.match(tarinfo.name):
                if logger.isEnabledFor(logging.DEBUG) and show_progress:
                    print(" "*80, file=sys.stderr, end="\r")
                debug("    # Extracting required file: %s", tarinfo.name)
                tar.extract(tarinfo, datadir)
                continue
            # otherwise treat it like a table
            name, _ = os.path.splitext(tarinfo.name)  # remove extension
            # remove partition portion
            name = name.partition('#P')[0]
            name = name.replace('/', '.')
            name = tablename.decode(name)
            if table_filter(name):
                if logger.isEnabledFor(logging.DEBUG):
                    print(" "*80, file=sys.stderr, end="\r")
                    debug("    # Excluding %s - excluded by table filters",
                          tarinfo.name)
                continue
            if logger.isEnabledFor(logging.DEBUG):
                print(" "*80, file=sys.stderr, end="\r")
                debug("    # Extracting %s", tarinfo.name)
            tar.extract(tarinfo, datadir)
