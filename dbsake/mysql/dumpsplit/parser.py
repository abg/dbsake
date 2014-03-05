"""
dbsake.mysql.dumpsplit.parser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parse mysqldump files

"""
import collections

def extract_identifier(value):
    """Find a `quoted` identifier in value and return it"""
    # we attempt to find the starting and stopping `
    # and unquote the contents remaining
    idx0 = value.find('`')
    idx1 = value.rfind('`')
    # verify we actually found identifier markers
    if -1 in (idx0, idx1):
        raise ValueError("%r does not contain a valid identifier" % value)
    identifier = value[idx0+1:idx1]
    return identifier.replace('``', '`')

def categorize_section(line):
    """Based on a mysqldump comment "-- ...", categorize the section"""
    if line.startswith('-- Position'):
        section_type = 'replication_info'
    elif line.startswith('-- Table structure'):
        section_type = 'table_definition'
    elif line.startswith('-- Temporary table structure'):
        section_type = 'view_temporary_definition'
    elif line.startswith('-- Dumping data for table'):
        section_type = 'table_data'
    elif line.startswith('-- Current Database'):
        section_type = 'schema'
    elif line.startswith('-- Dumping routines'):
        section_type = 'schema_routines'
    elif line.startswith('-- Dumping events'):
        section_type = 'schema_events'
    elif line.startswith('-- Final view structure'):
        section_type = 'view_definition'
    elif line.startswith('/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;'):
        section_type = 'footer'
    elif line.startswith('-- Dump completed'):
        section_type = 'dump_completed'
    else:
        raise ValueError("Unknown section %s" % line)

    return section_type

def parse_section(parser):
    "Generic parse section algorithm"
    # iteratorate over a parser to grab the entirety of the CREATE TABLE portion
    #  of a section

    # essentially read 3 lines, stop once we hit a newline or another comment
    # XXX: This may be problematic for routines/events with embedded comments
    yield next(parser) # --
    yield next(parser) # -- Table structure for table `...`
    yield next(parser) # --
    for line in parser:
        if line.startswith('--'):
            # read too far, requeue and abort
            parser.push(line)
            break
        if line.startswith('/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;'):
            parser.push(line)
            break
        yield line
    raise StopIteration

def read_section_header(parser):
    """Read the next section header and return the type

    All read lines are pushed back onto the parser stack
    for future reads and only the identifier classifying
    the next block is returned
    """
    cached = []
    for line in parser:
        cached.append(line)
        try:
            section_type = categorize_section(line)
        except ValueError:
            continue
        else:
            break
    else:
        if not cached:
            raise StopIteration
        raise ValueError("Failed to categorize input. cached=%r" % (cached,))
    for line in cached:
        parser.push(line)
    return section_type

class MySQLDumpParser(object):
    """Parse a mysqldump stream

    This assumes a non-compact dump with commented sections
    used as 'waypoints' to classify each range of content.
    """
    def __init__(self, stream):
        self.stream = stream
        self._header = None
        self.cache = collections.deque()
        self._context = dict(db=None, tbl=None)

    def __iter__(self):
        return self

    def __next__(self):
        if self.cache:
            return self.cache.popleft()
        else:
            return next(self.stream)
    # python 2.x shim.
    next = __next__

    def push(self, line):
        """Push an input line back onto the parser"""
        self.cache.append(line)

    @property
    def header(self):
        """Reader the header from the stream"""
        if not self._header:
            # assume no lines have yet been read
            header = []
            # read -- header comments
            line = next(self)
            while line.strip():
                header.append(line)
                line = next(self)
            header.append(line) # append newline

            # read /* -- */ session initialization
            line = next(self)
            while line.strip():
                if not (line.startswith('--') or line.startswith('/*!')):
                    raise ValueError("Unexpected header line: %s" % line)
                header.append(line)
                line = next(self)
            header.append(line)
            self._header = ''.join(header)
        for line in self._header.splitlines(True):
            yield line

    @property
    def sections(self):
        """Iterate over the sections of the dump file

        yields section_type, iteratorator pairs

        Where section_type is a string denoting what sort
        of data the iteratorator will emit.  One of:
            * header - initial comments and import session variables
            * replication_info - CHANGE MASTER command
            * table_definition - CREATE TABLE statements
            * view_temporary_definition - temporary MyISAM table stub for
                                          a view definition
            * table_data - INSERT/REPLACE statements to populate a table
            * schema - CREATE DATABASE statement section
            * schema_routines - PROCEDURE/FUNCTIONS for a database
            * schema_events - EVENTS defined in a database
            * view_definition - VIEW definition - drops temporary stub table
                                and creates the actual view
            * footer - restore session variables
            * dump_completed - final "-- Dump completed ..." comment line

        """
        # read first three lines to get a section header
        # based on that return a parser that yields lines
        # from the following section
        # currently uses the generic parse_section(parser) method
        # may introduce other methods for more specialized parsing
        # in the future
        if not self._header:
            yield 'header', self.header

        # read three lines
        while not self.stream.closed:
            section_type = read_section_header(self)
            yield section_type, parse_section(self)
