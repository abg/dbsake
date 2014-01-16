"""
dbsake.upgrademycnf
~~~~~~~~~~~~~~~~~~~

"""
from __future__ import print_function

import difflib
import os
import sys

from dbsake import baker

@baker.command(name='upgrade-mycnf',
               shortopts=dict(config="c",
                              target="t",
                              patch="p"))
def upgrade_mycnf(config='/etc/my.cnf',
                  target='5.5',
                  patch=False):
    """Patch a my.cnf to a new MySQL version

    :param config: my.cnf file to parse (default: /etc/my.cnf)
    :param target: MySQL version to target the option file (default: 5.5)
    :param patch: Output unified diff rather than full config (default off)
    """
    from dbsake.util import relpath
    from dbsake.upgrademycnf import parser

    if target == '5.1':
        rewriter = parser.MySQL51OptionRewriter
    elif target == '5.5':
        rewriter = parser.MySQL55OptionRewriter
    elif target == '5.6':
        rewriter = parser.MySQL56OptionRewriter
    elif target == '5.7':
        rewriter = parser.MySQL57OptionRewriter
    else:
        print("Invalid target version '%s'" % target, file=sys.stderr)
        return 1

    if not os.path.exists(config):
        print("No config file found: %s" % config, file=sys.stderr)
        return 1

    for path, orig, modified in parser.upgrade_config(config, rewriter):
        if patch:
            # make patch file names pretty
            from_file = relpath(os.path.abspath(path), '/')
            to_file = os.path.join('b', from_file)
            from_file = os.path.join('a', from_file)
            print(''.join(difflib.unified_diff(orig, modified, from_file, to_file)))
        else:
            print(''.join(modified))
    return 0
