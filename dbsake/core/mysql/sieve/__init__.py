"""
dbsake.core.mysql.sieve
~~~~~~~~~~~~~~~~~~~~~~~

Filtering API for mysqldump files
"""
from __future__ import unicode_literals

import collections
import logging

from dbsake.util import dotdict
from dbsake.util import pathutil

from . import exc
from . import parser
from . import filters
from . import transform
from . import writers

Error = exc.SieveError

info = logging.info


class Options(dotdict.DotDict):
    def __init__(self, *args, **kwargs):
        super(Options, self).__init__(*args, **kwargs)
        self.setdefault('sections', [])
        self.setdefault('exclude_sections', [])

    def exclude_section(self, name):
        self.exclude_sections.append(name)


def sieve(options):
    if options.output_format == 'directory':
        pathutil.makedirs(options.directory, exist_ok=True)

    if not options.table_data:
        options.exclude_section('tabledata')

    dump_parser = parser.DumpParser(stream=options.input_stream)
    filter_section = filters.SectionFilter(options)
    transform_section = transform.SectionTransform(options)
    write_section = writers.load(options, context=transform_section)

    stats = collections.defaultdict(int)

    for section in dump_parser:
        if filter_section(section):
            continue
        stats[section.name] += 1
        transform_section(section)
        write_section(section)

    info("Processed %s. Output: %d database(s) %d table(s) and %d view(s)",
         options.input_stream.name,
         stats['createdatabase'] or 1,
         stats['tablestructure'],
         stats['view'])
