"""
dbsake.core.mysql.frm.keys
~~~~~~~~~~~~~~~~~~~~~~~~~~

Support for decoding index data from a .frm

"""
from __future__ import unicode_literals

import collections
from . import util

try:
    _range = xrange
except NameError:
    _range = range

HA_NOSAME = 1  # Set if not dupplicated records
HA_PACK_KEY = 2  # Pack string key to previous key
HA_AUTO_KEY = 16
HA_BINARY_PACK_KEY = 32  # Packing of all keys to prev key
HA_FULLTEXT = 128  # For full-text search
HA_UNIQUE_CHECK = 256  # Check the key for uniqueness
HA_SPATIAL = 1024  # For spatial search
HA_NULL_ARE_EQUAL = 2048  # NULL in key are cmp as equal
HA_USES_COMMENT = 4096
HA_USES_PARSER = 16384  # Fulltext index uses [pre]parser
HA_GENERATED_KEY = 8192  # Automaticly generated key


# /* The combination of the above can be used for key type comparison. */
# #define HA_KEYFLAG_MASK (HA_NOSAME | HA_PACK_KEY | HA_AUTO_KEY |
#                          HA_BINARY_PACK_KEY | HA_FULLTEXT | HA_UNIQUE_CHECK |
#                         HA_SPATIAL | HA_NULL_ARE_EQUAL | HA_GENERATED_KEY)

HA_KEY_ALG_UNDEF = 0  # Not specified (old file)
HA_KEY_ALG_BTREE = 1  # B-tree, default one
HA_KEY_ALG_RTREE = 2  # R-tree, for spatial searches
HA_KEY_ALG_HASH = 3  # HASH keys (HEAP tables)
HA_KEY_ALG_FULLTEXT = 4  # FULLTEXT (MyISAM tables)

HA_KEY_ALGO = {
    HA_KEY_ALG_UNDEF: '',
    HA_KEY_ALG_BTREE: 'BTREE',
    HA_KEY_ALG_RTREE: 'RTREE',
    HA_KEY_ALG_HASH: 'HASH',
    HA_KEY_ALG_FULLTEXT: 'FULLTEXT',
}


class Key(collections.namedtuple('Key',
                                 'name parts algorithm block_size '
                                 'index_type is_unique parser comment')):
    maybe_prefix_types = set([
        'VARCHAR',
        'VAR_STRING',
        'STRING',
    ])

    always_prefix_types = set([
        'TINY_BLOB',
        'MEDIUM_BLOB',
        'LONG_BLOB',
        'BLOB',
        'GEOMETRY',
    ])

    def _format_key_part(self, part):
        # format the basic column name being indexed
        value = part.format()
        if self.index_type in ('FULLTEXT', 'SPATIAL'):
            # FULLTEXT / SPATIAL may never have an index prefix
            return value
        elif (part.column.type_code.name in self.maybe_prefix_types
                and part.length != part.column.length) or \
             (part.column.type_code.name in self.always_prefix_types):
                prefix_length = part.length // part.column.charset.maxlen
                value += '({0})'.format(prefix_length)
        return value

    def format(self):
        components = []
        if self.name == 'PRIMARY':
            components.append('PRIMARY KEY')
        elif self.is_unique:
            components.append('UNIQUE KEY')
        elif self.index_type == 'FULLTEXT':
            components.append('FULLTEXT KEY')
        elif self.index_type == 'SPATIAL':
            components.append('SPATIAL KEY')
        else:
            components.append('KEY')

        if self.name and self.name != 'PRIMARY':
            components.append("`{0}`".format(self.name))

        columns = '({0})'.format(','.join(self._format_key_part(part)
                                          for part in self.parts))
        components.append(columns)

        if self.algorithm:
            components.append('USING {0}'.format(self.algorithm))
        if self.block_size:
            components.append('KEY_BLOCK_SIZE={0}'.format(self.block_size))
        if self.comment:
            components.append("COMMENT '{0}'".format(self.comment))
        if self.parser not in (None, True):
            # note mysql outputs this with a single trailing whitespace
            components.append('/*!50100 WITH PARSER `%s` */ ' % self.parser)
        return ' '.join(components)


class KeyPart(collections.namedtuple('KeyPart', 'column length')):
    def format(self):
        return "`{0}`".format(self.column.name)


BYTES_PER_KEY = 8
BYTES_PER_KEY_PART = 9


def unpack_key_parts(parts_count, keyinfo, columns):
    for _ in _range(parts_count):
        fieldnr = keyinfo.uint16() & 0x3fff
        keyinfo.uint16() - 1  # offset
        keyinfo.uint8()  # flags
        keyinfo.uint16()  # key_type
        length = keyinfo.uint16()
        yield KeyPart(column=columns[fieldnr - 1], length=length)


def unpack_key_names_and_comments(key_extra_info):
    names, comments = key_extra_info.split(b'\x00', 1)
    names = tuple(name.decode('utf8') for name in names.split(b'\xff') if name)
    comments = util.ByteReader(comments)
    return names, comments


def unpack_keys(keyinfo, columns, parser_info=None):
    """Unpack index data from the raw key_info buffer

    :param columns: ``Column`` instances that refer to the associated table's
                    columns
    :returns: list of ``Key`` Instances
    """
    keyinfo = util.ByteReader(keyinfo)
    key_count = keyinfo.uint8()
    if key_count < 128:
        key_parts_count = keyinfo.uint8()
        keyinfo.skip(2)
    else:
        key_count = (key_count & 0x7f) | (keyinfo.uint8() << 7)
        key_parts_count = keyinfo.uint16()
    key_extra_length = keyinfo.uint16()

    # names, comments are calculated upfront so we can build the key as we go
    offset = (keyinfo.tell() + key_count*BYTES_PER_KEY +
              key_parts_count * BYTES_PER_KEY_PART)
    key_extra_info = keyinfo.read_at(offset=offset, size=key_extra_length)
    names, comments = unpack_key_names_and_comments(key_extra_info)

    for keyname in names:
        flags = keyinfo.uint16() ^ HA_NOSAME
        keyinfo.uint16()  # length
        parts_count = keyinfo.uint8()
        algorithm = HA_KEY_ALGO[keyinfo.uint8()]
        key_block_size = keyinfo.uint16()
        comment = None
        if flags & HA_USES_COMMENT:
            comment = comments.bytes_prefix16()
            comment = comment.decode('utf-8')
        if flags & HA_USES_PARSER:
            parser = parser_info.bytes0()
            parser = parser.decode('utf-8')
        else:
            parser = None
        parts = unpack_key_parts(parts_count, keyinfo, columns)

        if flags & HA_FULLTEXT:
            index_type = 'FULLTEXT'
        elif flags & HA_SPATIAL:
            index_type = 'SPATIAL'
        elif algorithm == 'HASH':
            index_type = 'HASH'
        else:
            index_type = 'BTREE'

        yield Key(
            name=keyname,
            parts=tuple(parts),
            algorithm=algorithm,
            block_size=key_block_size,
            parser=parser,
            comment=comment,
            index_type=index_type,
            is_unique=bool(flags & HA_NOSAME)
        )
