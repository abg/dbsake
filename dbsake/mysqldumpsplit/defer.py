#!/usr/bin/env python2.6

import csv
import io
import logging
import re

def extract_create_table(table_structure):
    result = []
    for line in table_structure.splitlines(True):
        if line.startswith('CREATE TABLE'):
            result.append(line)
        elif result:
            result.append(line)
            if line.rstrip().endswith(';'):
                break
    return ''.join(result)

KEY_CRE = re.compile(r'\s*KEY (?P<name>`.+`) \((?P<columns>.+)\),?$')

def extract_indexes(table_ddl):
    result = []
    for line in table_ddl.splitlines(True):
        match = KEY_CRE.match(line)
        if not match:
            continue
        result.append((parse_columns(match.group('name'))[0],
                       parse_columns(match.group('columns')),
                       line))
    return result


CONSTRAINT_CRE = re.compile(r'^\s*CONSTRAINT (?P<name>`.+`) FOREIGN KEY '
                            r'\((?P<columns>.+)\) REFERENCES')

def extract_constraints(table_ddl):
    result = []
    for line in table_ddl.splitlines(True):
        match = CONSTRAINT_CRE.match(line)
        if not match:
            continue
        result.append((parse_columns(match.group('name'))[0],
                       parse_columns(match.group('columns')),
                       line))
    return result

def parse_columns(value):
    reader = csv.reader(io.BytesIO(value),
                        quotechar='`',
                        skipinitialspace=True)
    return tuple(column for row in reader for column in row)

IDENT_CRE = re.compile(r'CREATE TABLE `(?P<name>.+)` \($')

def extract_table_name(table_ddl):
    for line in table_ddl.splitlines():
        match = IDENT_CRE.match(line)
        if match:
            return match.group('name')
    raise ValueError("Failed to find table name from DDL: %s" % table_ddl)

def format_alter_table(table_ddl, indexes):
    table = extract_table_name(table_ddl)
    lines = [line.strip() for _, _, line in indexes]
    if not lines: return ""

    ddl = "ALTER TABLE `{0}`\n    ADD ".format(table) + "\n    ADD ".join(lines)
    return ddl.rstrip(',') + ';'

def format_create_table(table_ddl, indexes):
    result = []
    deferred_lines = set(line for _, _, line in indexes)
    for line in table_ddl.splitlines(True):
        # this intends to strip trailing commas on lines
        # just before the closing parentheses to ensure
        # valid syntax even if we just dropped some 
        # indexes or constraints
        if line.startswith(')'):
            eol = result[-1][-1]
            result[-1] = result[-1].rstrip().rstrip(",") + eol
        if line not in deferred_lines:
            result.append(line)
    return ''.join(result)

def split_indexes(table_ddl, defer_constraints=False):
    keys = []
    constraints = []
    split_ddl = table_ddl.splitlines(True)
    indexes = extract_indexes(table_ddl)
    constraints = extract_constraints(table_ddl)


    if not defer_constraints:
        preserved_indexes = set()
        for constraint_name, constraint_columns, constraint_line in constraints:
            # read the indexes in sorted order - sorted by number of columns
            # flag the first matching index we find and move on to the next constraint.

            for name, columns, line in sorted(indexes, key=lambda x: len(x[1])):
                # if this index is a prefix to the constraint
                if columns[0:len(constraint_columns)] == constraint_columns:
                    preserved_indexes.add((name, columns, line, constraint_name))
                    break

        for name, columns, line, constraint in preserved_indexes:
            logging.warn("Not deferring index `%s` - used by constraint `%s`",
                         name, constraint)
            indexes.remove((name, columns, line))
    else:
        indexes += constraints

    return (format_alter_table(table_ddl, indexes),
            format_create_table(table_ddl, indexes))

if __name__ == '__main__':
    create_table = '''
CREATE TABLE `child` (
  `parent_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`parent_id`),
  CONSTRAINT `child_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `parent` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
'''

    table_ddl = extract_create_table(create_table)
    alter_table, table_ddl = split_indexes(table_ddl, defer_constraints=True)
    print "ALTER"
    print alter_table
    print
    print "CREATE"
    print table_ddl
    print

