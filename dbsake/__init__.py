"""
dbsake
~~~~~~

"""
from __future__ import print_function

import codecs
import functools
import logging
import optparse
import os
import pkgutil
import sys

try:
    _basestring = basestring
except NameError:
    _basestring = str

__version__ = '1.0.4-dev'

from dbsake import baker

def discover_commands():
    walk_packages = pkgutil.walk_packages
    for importer, name, is_pkg in walk_packages(__path__, __name__ + '.'):
        if not is_pkg: continue
        # don't autoload third party packages
        if 'sarge' in name or 'tempita' in name: continue
        logging.debug("Attempting to load module '%s'", name)
        loader = importer.find_module(name, None)
        loader.load_module(name)

def log_level(name):
    try:
        return logging._levelNames[name.upper()]
    except KeyError:
        raise ValueError("Invalid logging level '%s'", name)

def main():
    sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    parser = optparse.OptionParser(prog='dbsake')
    valid_log_levels = [name.lower() for name in logging._levelNames
                        if isinstance(name, _basestring) and 
                           name is not 'NOTSET']
    parser.add_option('-V', '--version',
                      action='store_true',
                      help="show dbsake version and exit")
    parser.add_option('-l', '--log-level',
                      choices=valid_log_levels,
                      metavar='<log-level>',
                      help="Choose a log level; default: info",
                      default='info')
    parser.disable_interspersed_args()
    opts, args = parser.parse_args()

    if opts.version:
        print("dbsake v" + __version__)
        return 0

    logging.basicConfig(format="%(asctime)s %(message)s",
                        level=log_level(opts.log_level))
    discover_commands()
    try:
        return baker.run(argv=['dbsake'] + args, main=False)
    except baker.TopHelp:
        baker.usage()
        return os.EX_USAGE
    except baker.CommandHelp as exc:
        baker.usage(exc.cmd)
        return os.EX_USAGE
    except baker.CommandError as exc:
        logging.info("%s", exc)
        return os.EX_SOFTWARE
    except KeyboardInterrupt:
        logging.info("Interrupted")
        return os.EX_SOFTWARE
    except:
        # uncaught exception
        logging.fatal("Uncaught exception.", exc_info=True)
        logging.fatal("Please file a bug at github.com/abg/dbsake/issues")
        return os.EX_SOFTWARE

if __name__ == '__main__':
    sys.exit(main())
