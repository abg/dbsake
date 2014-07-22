"""
dbsake.core.mysql.sieve.filters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

mysqldump section filtering
"""

import fnmatch
import logging

debug = logging.debug


class SectionFilter(object):
    def __init__(self, options):
        self.options = options

    def filtered_section(self, section):
        include_sections = self.options.sections
        exclude_sections = self.options.exclude_sections
        name = section.name

        if include_sections and name not in include_sections:
            debug("# list of sections to include specified and '%s' was "
                  "not found. Filtering.", name)
            return True
        if name in exclude_sections:
            debug("# '%s' was in the list of excluded sections", name)
            return True
        return False

    def filtered_table(self, section):
        if not section.database:
            debug("# No database context, skipping table filters")
            return False

        identifier = b'.'.join([section.database or b'', section.table or b''])
        identifier = identifier.decode('utf-8')

        for pattern in self.options.exclude_table:
            if fnmatch.fnmatch(identifier, pattern):
                debug("# '%s' matched table exclusion pattern %s. "
                      "Filtering", identifier, pattern)
                return True

        for pattern in self.options.table:
            if fnmatch.fnmatch(identifier, pattern):
                debug("# '%s' matched a table inclusion pattern(%s). "
                      "Including.", identifier, pattern)
                return False

        debug("# '%s' did not match any inclusion pattern. Filtering.", identifier)
        return True if self.options.table else False

    def __call__(self, section):
        if self.filtered_section(section) or self.filtered_table(section):
            section.flush()
            return True
        else:
            return False
