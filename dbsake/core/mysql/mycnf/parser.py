"""
dbsake.core.mysql.mycnf.parser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


MySQL my.cnf parsing and rewriting support

"""
from __future__ import unicode_literals

import codecs
import glob
import logging
import os
import re
import string

# options we might validly see multiple times in a mysql section
# used to not warn so harshly about duplicates in this case
multi_valued_options = (
    'binlog-do-db',
    'binlog-ignore-db',
    'replicate-do-db',
    'replicate-ignore-db',
    'replicate-do-table',
    'replicate-ignore-table',
    'replicate-wild-do-table',
    'replicate-wild-ignore-table',
    'plugin-load',
)


# basic parsing helper methods
# borrowed from holland.lib.mysql's option parsing package
def remove_inline_comment(value):
    """Remove a MySQL inline comment from an option file line"""
    escaped = False
    quote = None
    for idx, char in enumerate(value):
        if char in ('"', "'") and not escaped:
            if not quote:
                quote = char
            elif quote == char:
                quote = None
        if not quote and char == '#':
            return value[0:idx], value[idx:]
        escaped = (quote and char == '\\' and not escaped)
    return value, ''


def unpack_option_value(value):
    """Process an option value according to MySQL's syntax rules"""
    value, comment = remove_inline_comment(value)
    value = value.strip()
    return value, comment


def resolve_option(item):
    """Expand an option prefix to the full name of the option"""
    known = [
        u'host',
        u'password',
        u'port',
        u'socket',
        u'user',
    ]
    candidates = [key for key in known if key.startswith(item)]

    if len(candidates) > 1:
        # mimic MySQL's error message
        raise ValueError("ambiguous option '%s' (%s)" %
                         (item, ','.join(candidates)))
    elif not candidates:
        return item

    return candidates[0]

SV_CRE = re.compile(r'(?P<sv>set[-_]variable\s*=\s*)(?P<value>.*)')


def sanitize(line, lineno):
    """Sanitize an old set-variable option to modern key=value form"""
    match = SV_CRE.match(line)
    if match:
        value = match.group('value')
        logging.info("Rewrote obsolete syntax %r to %r on line %d",
                     line.rstrip(), value.rstrip(), lineno)
        return value
    return line

KV_CRE = re.compile(r'\s*(?P<key>[^=\s]+?)\s*(?:=\s*(?P<value>.*))?$')


def parse_option(line):
    """Process a key/value directive according to MySQL syntax rules

    :returns: tuple if line is a valid key/value pair otherwise returns None
              If this is a bare option such as 'no-auto-rehash' the value
              element of the key/value tuple will be None
    """
    match = KV_CRE.match(line)
    if match:
        key, value = match.group('key', 'value')
        if value:
            value, inline_comment = unpack_option_value(value)
        else:
            key, inline_comment = remove_inline_comment(key)
        key = resolve_option(key)
        return key, value, inline_comment
    return None


# Rewrite support
class RewriteRule(object):
    """Rewrite an option into zero or more options

    :attr options: list of lines to rewrite some option into

    Each option may have a ${value} or ${key} macro which
    will be replaced by the original value or option name
    (respectively)

    :attr reason: an optional reason that will be logged when
                  rewriting an option

    >>> noop_rule = RewriteRule([], reason='Stupid option.')
    >>> for line in noop_rule.rewrite('skip-innodb', None):
    ...     print line
    [INFO] Rewriting option '%s'.  Reason: Stupid option.
    """
    def __init__(self, options=None, reason='unknown'):
        self.options = options
        self.reason = reason

    def __call__(self, key, value):
        if self.options:
            action = 'Rewriting'
        else:
            action = 'Removing'
        logging.info("%s option '%s'. Reason: %s", action, key, self.reason)

        for option in self.options:
            yield string.Template(option).safe_substitute(key=key, value=value)


class SlowLogRewriteRule(RewriteRule):
    """Rewrite < 5.1 slow-query-log optoins"""
    def __call__(self, key, value):
        self.options = [
            'slow-query-log = 1',
            'slow-query-log-file = ${value}',
            'log-slow-slave-statements',
        ]
        if value is None:
            # don't output slow-query-log-file if a value wasn't previously set
            # we'll default to the same host_name-slow.log
            self.options.remove('slow-query-log-file = ${value}')
        for line in super(SlowLogRewriteRule, self).__call__(key, value):
            yield line


class InnoDBPluginRewriteRule(RewriteRule):
    """Rewrite innodb plugin loading options for MySQL 5.5+"""
    options = ()

    def __call__(self, key, value):
        # strip all ha_innodb_plugin.so references; leave anything else
        result = []
        for option in value.split(';'):
            plugin_data = option.split('=')
            if len(plugin_data) == 2:
                plugin_lib = plugin_data[1]
            else:
                plugin_lib = plugin_data[0]
            if plugin_lib != 'ha_innodb_plugin.so':
                result.append(option)
        if result:
            self.options = ['plugin-load = ' + ';'.join(result)]
        else:
            self.options = []
        for line in super(InnoDBPluginRewriteRule, self).__call__(key, value):
            yield line


class OptionRewriter(object):
    """Base OptionRewriter

    :attr rules: table (dict) of options -> RewriteRule

    """
    rules = {
    }

    @classmethod
    def rewrite(cls, key, value=None):
        """Rewrite an option according to a rule table

        :param key: option to rewrite
        :param value: original value for the option

        :returns: returns rewritten option list
        """
        try:
            rule = cls.rules[key]
        except KeyError:
            logging.debug("No rule to rewrite '%s'", key)
            return None

        return [line for line in rule(key, value)]


class MySQL51OptionRewriter(OptionRewriter):
    """Option Rewriter for MySQL 5.1 options"""

    rules = {
        'default-character-set': RewriteRule(
            ['character-set-server = ${value}'],
            reason="Deprecated in MySQL 5.0 in favor of character-set-server"),
        'default-collation': RewriteRule(
            ['collation-server = ${value}'],
            reason="Deprecated in MySQL 4.1.3 in favor of collation-server"),
        'default-table-type': RewriteRule(
            ['default-storage-engine = ${value}'],
            reason=("Deprecated in MySQL 5.0 in favor of "
                    "default-storage-engine")),
        'log-slow-queries': SlowLogRewriteRule(
            reason='Logging options changed in MySQL 5.1'
        ),
        'table-cache': RewriteRule([
            'table-open-cache = ${value}',
            'table-definition-cache = ${value}',
        ], reason='Table cache options changed in MySQL 5.1'),
        # null rules (completely removes from output)
        'enable-pstack': RewriteRule([
        ], reason='Deprecated in MySQL 5.1.54'),
        'log-long-format': RewriteRule([
        ], reason="Deprecated in MySQL 4.1"),
        'log-short-format': RewriteRule([
        ], reason="Deprecated in MySQL 4.1. This option now does nothing."),
        'master-connect-retry': RewriteRule([
        ], reason='Deprecated in MySQL 5.1.17. Removed in 5.5'),
        'master-host': RewriteRule([
        ], reason='Deprecated in MySQL 5.1.17. Removed in 5.5'),
        'master-password': RewriteRule([
        ], reason='Deprecated in MySQL 5.1.17. Removed in 5.5'),
        'master-port': RewriteRule([
        ], reason='Deprecated in MySQL 5.1.17. Removed in 5.5'),
        'master-user': RewriteRule([
        ], reason='Deprecated in MySQL 5.1.17. Removed in 5.5'),
        'master-ssl': RewriteRule([
        ], reason='Deprecated in MySQL 5.1.17. Removed in 5.5'),
        'safe-mode': RewriteRule([
        ], reason="Deprecated in MySQL 5.0"),
        'safe-show-database': RewriteRule([
        ], reason="Deprecated in MySQL 4.0.2"),
        'skip-locking': RewriteRule([
        ], reason='Deprecated in MySQL 4.0.3. Removed in 5.5'),
        'skip-external-locking': RewriteRule([
        ], reason='Default behavior in MySQL 4.1+'),
        'skip-bdb': RewriteRule([
        ], reason='Removed in MySQL 5.1.11'),
        'skip-innodb': RewriteRule([
        ], reason='Default storage engine in 5.5'),
        'skip-thread-priority': RewriteRule([
        ], reason="Deprecated in MySQL 5.1.29"),
    }


class MySQL55OptionRewriter(MySQL51OptionRewriter):
    """Rewrite rules for MySQL 5.5 my.cnfs

    Inherits all of the rules from 5.1, but also
    handles deprecating innodb plugin options
    (builtin to 5.5 now) and thread-handling=one-thread
    """
    rules = dict(MySQL51OptionRewriter.rules)
    rules['one-thread'] = RewriteRule([
        '--thread-handling=no-threads',
    ], reason="Deprecated and removed in MySQL 5.6")
    rules['ignore-builtin-innodb'] = RewriteRule(
        options=[],
        reason="InnoDB plugin is now the default in 5.5")
    rules["plugin-load"] = InnoDBPluginRewriteRule(
        reason="InnoDB plugin is now the default in 5.5")


class MySQL56OptionRewriter(MySQL55OptionRewriter):
    """MySQL 5.6 option rewriting rules

    Currently this is identical to 5.5

    XXX: 5.6 has deprecated option prefixes
    XXX: other 5.6 deprecated options?
    """
    rules = dict(MySQL55OptionRewriter.rules)


class MySQL57OptionRewriter(MySQL56OptionRewriter):
    """MySQL 5.7 rewriting rules

    Currently this is identical to 5.6
    """
    rules = dict(MySQL55OptionRewriter.rules)


def parse(path):
    """Parse an iterable of lines into a list and option mapping

    :returns: tuple list, option-mapping

    option-mapping is a table of option-name -> list of offsets
    where list-of-offsets notes where in the list of lines the option
    can be found.  If an option is repeated multiple times it will
    have multiple entries in the option-mapping table.
    """
    # remaining !included .cnf to worry about
    paths = [path]
    while paths:
        with codecs.open(paths.pop(0), 'rb', 'utf-8') as iterable:
            section = None
            lines = []
            # map interesting options -> offsets in lines[]
            keys = {}
            for idx, line in enumerate(iterable):
                lines.append(line)
                # trim righ-trailing whitespace
                # (preserve original line)
                _line = sanitize(line, idx+1).rstrip()
                if not _line:
                    # skip blank lines
                    continue
                if _line.startswith('['):
                    section = _line[1:-1]
                    continue

                if _line.startswith('#'):
                    continue

                if _line.startswith('!include '):
                    paths.append(_line.split(None, 2)[-1])
                    continue

                if _line.startswith('!includedir '):
                    _path = os.path.join(_line.split(None, 2)[-1], '*.cnf')
                    paths.extend(glob.glob(_path))
                    continue

                if section != 'mysqld':
                    logging.debug("Ignoring [%s] options %s on line %d",
                                  section, _line, idx+1)
                    continue
                # must be an option or a syntax error
                key, value, inline_comment = parse_option(_line)

                # normalize key
                # XXX: handle prefix-values
                # (e.g. key-buffer -> key-buffer-size)
                key = key.replace('_', '-')

                keys.setdefault(key, [])
                keys[key].append((idx, value, _line))

        yield iterable.name, lines, keys


def upgrade_config(path, rewriter):
    """Upgrade my.cnf based on set of rewriter rules

    Yields a tuple of three elements:
         (path_to_mycnf, iterable of origina lines, iterable of modified lines)

    path_to_mycnf will just be `path` in the trivial case of no !include*
    directives, but otherwise will yield a path for each found config
    in a !include directive.

    original_lines, modified_lines can be passed to difflib to generate
    diff output easily.  Otherwise, modified_lines may be joined by os.linesep
    to generate full output.

    :param path: path to my.cnf file
    :param rewrite: OptionRewriter instance with rules to handle options
    :yields: tuple of path, lines, modified_lines
    """
    for path, lines, keys in parse(path):
        purge_list = []
        pending = {}

        for key, idx_list in keys.items():
            if len(idx_list) > 1 and key != 'set-variable' and \
                    key not in multi_valued_options:
                logging.warning("Duplicate options for '%s'", key)
                for idx, _, _ in idx_list:
                    logging.warning("  - %d:%s", idx+1, lines[idx].rstrip())

            for idx, value, line in idx_list:
                options = rewriter.rewrite(key, value)
                if options is not None:
                    # push new options into pending
                    pending.setdefault(idx, [])
                    pending[idx].extend(options)
                elif line != lines[idx]:
                    pending.setdefault(idx, [line])

        result = []
        for idx, line in enumerate(lines):
            # skip lines we should completely purge
            if idx in purge_list:
                logging.warning("Removing option %d:%s", idx, line.rstrip())
                continue
            # replace lines we rewrite
            if idx in pending:
                logging.debug("Rewriting %d:%s", idx, line.rstrip())
                for line in pending[idx]:
                    logging.debug("  + %s", line)
                    result.append(line + '\n')
            else:
                # otherwise just output the original line
                result.append(line)
        yield path, lines, result
