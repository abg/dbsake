"""
dbsake.core.mysql.sandbox.datasource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Support for importing data sources

"""
from __future__ import print_function

import logging
import os
import time

from dbsake import pycompat
from dbsake.util import cmd

from dbsake.core.mysql import unpack

from . import common

info = logging.info
error = logging.error


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
    datasource = options.datasource

    if not datasource:
        return

    start = time.time()
    info("  Preloading sandbox data from %s", datasource)
    try:
        with open(datasource, 'rb') as fileobj:
            unpack.unpack(fileobj,
                          options.datadir,
                          options.include_tables,
                          options.exclude_tables,
                          options.report_progress)
    except unpack.UnpackError:
        error(" - Unsupported data source: %s", datasource)
        raise common.SandboxError("Unable to unpack provided datasource.")

    info("    * Data extracted in %.2f seconds", time.time() - start)

    ib_logfile = os.path.join(options.datadir, 'ib_logfile0')
    xb_logfile = os.path.join(options.datadir, 'xtrabackup_logfile')
    if not os.path.exists(ib_logfile) and os.path.exists(xb_logfile):
        info("    - Datadir '%s' appears to have unprepared "
             "Percona XtraBackup data", options.datadir)
        info("    - Preparing datadir via innobackupex --apply-log")
        start = time.time()
        prepare_datadir(options.datadir, options)
        info("    - Prepared datadir in %.2f seconds", time.time() - start)
