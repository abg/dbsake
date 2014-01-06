import codecs
import logging
import os
import pkgutil
import sys

try:
    _basestring = basestring
except NameError:
    _basestring = str

__version__ = '1.0.1'

from dbsake import argparse
from dbsake import baker

def discover_commands():
    walk_packages = pkgutil.walk_packages
    for importer, name, is_pkg in walk_packages(__path__, __name__ + '.'):
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
    parser = argparse.ArgumentParser()
    valid_log_levels = [name.lower() for name in logging._levelNames
                        if isinstance(name, _basestring) and name is not 'NOTSET']
    parser.add_argument('--version', '-V', action='version',
                        version='%(prog)s ' + __version__)
    parser.add_argument('-l', '--log-level',
                        choices=valid_log_levels,
                        help="Choose a log level; default: info",
                        default='info')
    parser.add_argument("cmd", nargs="...")
    opts = parser.parse_args()
    logging.basicConfig(format="%(asctime)s %(message)s",
                        level=log_level(opts.log_level))
    discover_commands()
    try:
        logging.debug("argv: %r", opts.cmd)
        return baker.run(argv=sys.argv[0:1] + opts.cmd, main=False)
    except baker.TopHelp:
        baker.usage()
        return os.EX_USAGE
    except baker.CommandHelp as exc:
        baker.usage(exc.cmd)
        return os.EX_USAGE
    except baker.CommandError as exc:
        logging.info("%s", exc)
        return os.EX_SOFTWARE
    except:
        # uncaught exception
        logging.fatal("Uncaught exception.", exc_info=True)
        logging.fatal("Please file a bug at github.com/abg/dbsake/issues")
        return os.EX_SOFTWARE

if __name__ == '__main__':
    sys.exit(main())
