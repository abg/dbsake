"""
dbsake.mysqldumpsplit
~~~~~~~~~~~~~~~~~~~~~

Command to split a mysqldump file into constituent parts

"""
from __future__ import print_function

import logging
import os
import re
import sys

from dbsake import baker
from dbsake.util import mkdir_safe
from dbsake.mysqldumpsplit.parser import MySQLDumpParser, extract_identifier
from dbsake.mysqldumpsplit.defer import extract_create_table, split_indexes

@baker.command(name='split-mysqldump')
def split_mysqldump(defer_indexes=False, defer_constraints=False):
    stream = sys.stdin
    parser = MySQLDumpParser(stream)
    header = None
    post_data = None
    for section_type, iterator in parser.sections:
        if section_type == 'replication_info':
            with open('replication_info.sql', 'wb') as fileobj:
                fileobj.write(header)
                for line in iterator:
                    fileobj.write(line)
        elif section_type == 'schema':
            lines = list(iterator)
            name = extract_identifier(lines[1])
            mkdir_safe(name)
            with open(os.path.join(name, 'create.sql'), 'wb') as fileobj:
                fileobj.write(header)
                for line in lines:
                    fileobj.write(line)
        elif section_type == 'schema_routines':
            with open(os.path.join(name, 'routines.sql'), 'wb') as fileobj:
                fileobj.write(header)
                for line in iterator:
                    fileobj.write(line)
        elif section_type == 'schema_events':
            with open(os.path.join(name, 'events.sql'), 'wb') as fileobj:
                fileobj.write(header)
                for line in iterator:
                    fileobj.write(line)
        elif section_type in ('table_definition',):
            lines = list(iterator)
            table_definition_data = ''.join(lines)
            table_ddl = extract_create_table(table_definition_data)
            if defer_indexes and 'ENGINE=InnoDB' in table_ddl:
                alter_table, create_table = split_indexes(table_ddl,
                                                          defer_constraints)
                logging.info("Would defer indexes/constraints as: %s",
                             alter_table)
                if alter_table:
                    table_definition_data = table_definition_data.replace(table_ddl, create_table)
                    post_data = alter_table
            table = extract_identifier(lines[1])
            with open(os.path.join(name, table + '.schema.sql'), 'wb') as fileobj:
                fileobj.write(header)
                fileobj.write(table_definition_data)
        elif section_type == 'table_data':
            comments = [next(iterator) for _ in xrange(3)]
            table = extract_identifier(comments[1])
            with open(os.path.join(name, table + '.data.sql'), 'wb') as fileobj:
                fileobj.write(header)
                for line in comments:
                    fileobj.write(line)
                for line in iterator:
                    fileobj.write(line)
                if post_data:
                    print("", file=fileobj)
                    print("--", file=fileobj)
                    print("-- InnoDB Fast index creation", file=fileobj)
                    print("--", file=fileobj)
                    print("", file=fileobj)
                    fileobj.write(post_data)
                    print("", file=fileobj)
                    post_data = None
        elif section_type == 'header':
            header = ''.join(list(iterator))
            match = re.search('Database: (?P<schema>.*)$', header, re.M)
            if match and match.group('schema'):
                name = match.group('schema')
                mkdir_safe(name)
        elif section_type in ('view_temporary_definition',
                              'view_definition'):
            with open(os.path.join(name, 'views.sql'), 'ab') as fileobj:
                for line in iterator:
                    fileobj.write(line)
        else:
            print("Skipping section type: %s"% (section_type,),
                  file=sys.stderr)
            # drain iterator, so we can continue
            for line in iterator:
                continue
    return 0


