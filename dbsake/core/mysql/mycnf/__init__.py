"""
dbsake.core.mysql.mycnf
~~~~~~~~~~~~~~~~~~~~~~~

"""
from __future__ import print_function

import difflib
import os
import sys

from dbsake.util import path

from . import parser

class Error(Exception):
    """Raised if error parsing my.cnf"""

def upgrade(config, target, patch):
    """Patch a my.cnf to a new MySQL version

    :param config: my.cnf file to parse (default: /etc/my.cnf)
    :param target: MySQL version to target the option file (default: 5.5)
    :param patch: Output unified diff rather than full config (default off)
    """
    if target == '5.1':
        rewriter = parser.MySQL51OptionRewriter
    elif target == '5.5':
        rewriter = parser.MySQL55OptionRewriter
    elif target == '5.6':
        rewriter = parser.MySQL56OptionRewriter
    elif target == '5.7':
        rewriter = parser.MySQL57OptionRewriter
    else:
        raise Error("Invalid target version '%s'" % target)

    if not os.path.exists(config):
        raise Error("No config file found: %s" % config)

    for cfg_path, orig, modified in parser.upgrade_config(config, rewriter):
        if patch:
            # make patch file names pretty
            from_file = path.relpath(os.path.abspath(cfg_path), '/')
            to_file = os.path.join('b', from_file)
            from_file = os.path.join('a', from_file)
            return ''.join(difflib.unified_diff(orig, modified, from_file, to_file))
        else:
            return ''.join(modified)
    return 0
