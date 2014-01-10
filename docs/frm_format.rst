.. _frm_format:

Description of the .frm format
------------------------------

dbsake parses some undocumented / poorly documented formats for MySQL
which were decoded by inspecting the MySQL source code.  Here is a
detailed document that attempts to describe the details of such
formats for other who may hack on these parts of dbsake.

.frm fileinfo section
~~~~~~~~~~~~~~~~~~~~~

The fileinfo section consists of 64 bytes that encode information about
the rest of the .frm file and various table level options.

The table here describes the information each byte encodes.  Offsets are
from the beginning of the file.  All values are little-endian integer of the
size noted in the Length column.

+------------+----------------+----------------------------------------------+
| Offset     | Length (bytes) |                 Description                  |
+------+-----+                |                                              |
| Hex  | Dec |                |                                              |
+======+=====+================+==============================================+ 
| 0000 | 0   |  2 bytes       | "Magic" identifier                           | 
+------+-----+                | Always the byte sequence fe 01               | 
| 0001 | 1   |                |                                              | 
+------+-----+----------------+----------------------------------------------+ 
| 0002 | 2   | 1 byte         | .frm version [1]_                            | 
+------+-----+----------------+----------------------------------------------+ 
| 0003 | 3   | 1 byte         |  "legacy_db_type" [2]_                       | 
+------+-----+----------------+----------------------------------------------+
| 0004 | 4   | 2-bytes        | "names_length" - always 3 and not used       |
+------+-----+                | in recent MySQL.  MySQL 3.23 set this to 1   |
| 0005 | 5   |                |                                              |
+------+-----+----------------+----------------------------------------------+
| 0006 | 6   | 2-bytes        | IO_SIZE; Always 4096 (0010)                  |
+------+-----+                |                                              |
| 0007 | 7   |                |                                              |
+------+-----+----------------+----------------------------------------------+
| 0008 | 8   | 2-bytes        | number of "forms" in the .frm                |
+------+-----+                | Should always be 1, even back to 3.23        |
| 0009 | 9   |                |                                              |
+------+-----+----------------+----------------------------------------------+
| 000a | 10  | 4-bytes        | Not really used except in .frm creation      |
+------+-----+                | Purpose unclear, i guess for aligning        | 
| 000b | 11  |                | sections in the ancient unireg format        |
+------+-----+                |                                              |
| 000c | 12  |                |                                              |
+------+-----+                |                                              |
| 000d | 13  |                |                                              |
+------+-----+----------------+----------------------------------------------+
| 000e | 14  | 2-bytes        | "tmp_key_length"; if equal to 0xffff then    |
+------+-----+                | the key length is a 4-byte integer at offset |
| 000f | 15  |                | 0x002f                                       |
+------+-----+----------------+----------------------------------------------+
| 0010 | 16  | 2-bytes        | "rec_length" - this is the size of the byte  |
+------+-----+                | string where default values are stored       |
| 0011 | 17  |                | See Default Values                           | 
+------+-----+----------------+----------------------------------------------+
| 0012 | 18  | 4-bytes        | Table MAX_ROWS=N opton                       |
+------+-----+                |                                              |
| 0013 | 19  |                |                                              |
+------+-----+                |                                              |
| 0014 | 20  |                |                                              |
+------+-----+                |                                              |
| 0015 | 21  |                |                                              |
+------+-----+----------------+----------------------------------------------+
| 0016 | 22  | 4-bytes        |  Table MIN_ROWS=N option                     |
+------+-----+                |                                              |
| 0017 | 23  |                |                                              |
+------+-----+                |                                              |
| 0018 | 24  |                |                                              |
+------+-----+                |                                              |
| 0019 | 25  |                |                                              |
+------+-----+----------------+----------------------------------------------+
| 001a | 26  | 1-byte         | Unused - always zero in 3.23 through 5.6     |
+------+-----+----------------+----------------------------------------------+
| 001b | 27  | 1-byte         | Always 2 - "// Use long pack-fields"         |
+------+-----+----------------+----------------------------------------------+
| 001c | 28  | 2-bytes        | key_info_length - size in bytes of the       |
+------+-----+                | keyinfo section                              |
| 001d | 29  |                |                                              |
+------+-----+----------------+----------------------------------------------+
| 001e | 30  | 2-bytes        | create_info->table_options                   |
+------+-----+                | See HA_OPTION_* values in include/my_base.h  |
| 001f | 31  |                |                                              |
+------+-----+----------------+----------------------------------------------+
| 0020 | 32  | 1-byte         | Unused; comment "// No filename anymore"     |
+------+-----+----------------+----------------------------------------------+
| 0021 | 33  | 1-byte         | 5 in 5.0+ comment "// Mark for 5.0 frm file" |
+------+-----+----------------+----------------------------------------------+
| 0022 | 34  | 4-bytes        | Table AVG_ROW_LENGTH option                  |
+------+-----+                |                                              |
| 0023 | 35  |                |                                              |
+------+-----+                |                                              |
| 0024 | 36  |                |                                              |
+------+-----+                |                                              |
| 0025 | 37  |                |                                              |
+------+-----+----------------+----------------------------------------------+
| 0026 | 38  | 1-byte         | Table DEFAULT CHARACTER SET option [3]_      |
+------+-----+----------------+----------------------------------------------+
| 0027 | 39  | 1-byte         | Unused [4]_                                  |
+------+-----+----------------+----------------------------------------------+
| 0028 | 40  | 1-byte         | Table ROW_FORMAT option                      |
+------+-----+----------------+----------------------------------------------+
| 0029 | 41  | 1-byte         | Unused; formerly Table RAID_TYPE option      |
+------+-----+----------------+----------------------------------------------+
| 002a | 42  | 1-byte         | Unused; formerly Table RAID_CHUNKS option    |
+------+-----+----------------+----------------------------------------------+
| 002b | 43  | 4-bytes        | Unused; formerly Table RAID_CHUNKSIZE option |
+------+-----+                |                                              |
| 002c | 44  |                |                                              |
+------+-----+                |                                              |
| 002d | 45  |                |                                              |
+------+-----+                |                                              |
| 002e | 46  |                |                                              |
+------+-----+----------------+----------------------------------------------+
| 002f | 47  | 4-bytes        | Size in bytes of the keyinfo section where   |
+------+-----+                | index metadata is defined                    |
| 0030 | 48  |                |                                              |
+------+-----+                |                                              |
| 0031 | 49  |                |                                              |
+------+-----+                |                                              |
| 0032 | 50  |                |                                              |
+------+-----+----------------+----------------------------------------------+
| 0033 | 51  | 4-bytes        | MySQL version encoded as a 4-byte integer in |
+------+-----+                | little endian format. This is the value      |
| 0034 | 52  |                | MYSQL_VERSION_ID from include/mysql_version.h|
+------+-----+                | in the mysql source tree.                    |
| 0035 | 53  |                | Example:                                     |
+------+-----+                | '\xb6\xc5\x00\x00'                           |
| 0036 | 54  |                | 0x0000c5b6 => 50614 => MySQL v5.6.14         | 
+------+-----+----------------+----------------------------------------------+
| 0037 | 55  | 4-bytes        | Size in bytes of table "extra info"          |
+------+-----+                |                                              |
| 0038 | 56  |                |  - CONNECTION=<string> (FEDERATED tables)    |
+------+-----+                |  - ENGINE=<string>                           |
| 0039 | 57  |                |  - PARTITION BY clause + partitioning flags  |
+------+-----+                |  - WITH PARSER names (MySQL 5.1+)            |
| 003a | 58  |                |  - Table COMMENT [5]_                        |
+------+-----+----------------+----------------------------------------------+
| 003b | 59  | 2-byte         | extra_rec_buf_length                         |
+------+-----+                |                                              |
| 003c | 60  |                |                                              |
+------+-----+----------------+----------------------------------------------+
| 003d | 61  | 1-byte         | Storage engine if table is partitioned [6]_  |
+------+-----+----------------+----------------------------------------------+
| 003e | 62  | 2-bytes        | Table KEY_BLOCK_SIZE option                  |
+------+-----+                |                                              |
| 003f | 63  |                |                                              |
+------+-----+----------------+----------------------------------------------+

.. [1] This is defined as FRM_VER+3+ test(create_info->varchar) in 5.0+
        Where FRM_VER is defined as 6, so the frm version will be either 9
        or 10 depending on if the table has varchar columns

.. [2] Maps to an enum value from "enum legacy_db_type" in sql/handler.h

.. [3] Character set id maps to an id from INFORMATION_SCHEMA.COLLATIONS
        and encodes both the character set name and the collation

.. [4] In the source code, there is a comment indicating this byte will be
        used for TRANSACTIONAL and PAGE_CHECKSUM table options in the future

.. [5] The table comment is stored in one of two places in the .frm file
       If the comment size in bytes is < 255 this is stored in the forminfo
       Otherwise it will be estored in the extra info section after the
       fulltext parser names (if any)

.. [6] Numeric id that maps to a enum value from "enum legacy_db_type"
       in sql/handler.h, similar to legacy_db_type

Key info section
~~~~~~~~~~~~~~~~

The key info section should always start at offset 0x1000 (4096); this is 
obtained from the 2-byte integer in fileinfo header  at offset 6, but
in any version of MySQL in the past decade will be 4096.

The size in bytes of this section is obtained from the key_length - typically
this is 4-byte integer at offset 0x002f (47) in the header.  Older versions
of MySQL only allocated a 2-byte integer for this length, at offset 
0x000e (14). This old location will have the value 0xffff if the key info
length exceeds the capacity of a 2-byte integer.

The structure of this section consists of an initial header noting the
total number of keys, total number of key components and the size of
"extra" key data (namely index names and index comments). This is followed
by a group for each index defined in the table and then the extra data -
names for each index followed by an optional index comment strings.

The header is essentially three integers:

[key_count][key_parts_count][length of extra data]

Where key_count is the number of indexes this metdata describes,
      key_parts_count is the number of components across all indexes
      and the length of extra data indicates how many bytes the index
      names and comments uses.

key_count and key_parts_count may be either 1 or 2 bytes.  If the first
byte is > 128 then key_count and key_parts_count use two bytes, otherwise
they use one byte each.  The extra length is always a 2 byte integer.

The logic in dbsake is:

.. code-block:: python

    key_count = keyinfo.uint8()
    if key_count < 128:
        key_parts_count = keyinfo.uint8()
        keyinfo.skip(2)
    else:
        key_count = (key_count & 0x7f) | (keyinfo.uint8() << 7)
        key_parts_count = keyinfo.uint16()
    key_extra_length = keyinfo.uint16()

Each key metadata consists of 8 bytes and each key part consists of 9 bytes.
So the total length of the index metadata is calculated by the formula::

  key_count * 8 + key_parts_count * 9

And this is the offset, relative to the start of keyinfo section, where the
index names and comments are found.

Each index group consists of 8 bytes of key metadata followed by 9 bytes of 
metadata for each indexed column. 

+----------------------------------------------------------------------------+
| Index metadata (8 bytes)                                                   |
+===========+=========+======================================================+
| flags     | 2 bytes | key flags from include/my_base.h.                    |
+-----------+---------+------------------------------------------------------+
| length    | 2 bytes | length of the index                                  |
+-----------+---------+------------------------------------------------------+
| key parts | 1 byte  | number of columns covered by this index              |
+-----------+---------+------------------------------------------------------+
| algorithm | 1 byte  | Key algorithm - maps to enum value "enum ha_key_alg" |
+-----------+---------+------------------------------------------------------+
| unused    | 2 bytes |                                                      |
+-----------+---------+------------------------------------------------------+

Followed by 1 or more column index metadata:

+----------------------------------------------------------------------------+
| Column index metadata (9 bytes)                                            |
+==============+=========+===================================================+
| field number | 2 bytes | Which column is indexed                           |
+--------------+---------+---------------------------------------------------+
| offset       | 2 bytes | Offset into a MySQL datastructure (internal use)  |
+--------------+---------+---------------------------------------------------+
| unused       | 1 byte  |                                                   |
+--------------+---------+---------------------------------------------------+
| key_type     | 2 bytes | maps to enum ha_base_keytype                      |
+--------------+---------+---------------------------------------------------+
| length       | 2 bytes | length of this index component                    |
+--------------+---------+---------------------------------------------------+

The names and comments follow this data with names being separated by the byte
value 255 ('\\xff') and the names and comments sections being separated by a
null byte.  So this essentially looks like this sort of python bytestring:

.. code-block:: python
   
   b'\xffPRIMARY\xffix_column1\xff\x00<index comments>'

Index comments are length-prefixed strings.  So there is a 2 byte integer
(little-endian) followed by the specified number of bytes for each comment.

Index comments are not terribly common so this will often be empty.

Defaults Section
~~~~~~~~~~~~~~~~

Immediately after the keyinfo section there is a byte string that details
the defaults for each column.  So this starts at IO_SIZE + key_length,
which can be derived from the .frm header.

The format of this buffer is essentially::

  [null_map][encoded column data]

Where the null_map is 1 or more bytes, with a bit per-column that can be
nullable.  The total number of bytes will be::

  (null_column_count + 7 ) // 8

The first bit is always set and column bits start a 1 offset in the null
map.  If a bit is set for the current column then this indicates the the
default is null (ie. DEFAULT NULL).

If a column's default is not null, then its default data will be recorded
at some offset noted in the Column metadata (described elsewhere in this
document).  The actual data format depends on the column type.  This
basically breaks down into the following cases:

 * integer-types - little-endian integers of 1, 2, 3, 4 or 8 bytes
 * float/double - little endian IEEE 745 values
 * decimal - either ascii strings ("3.14") < MySQL 5.0, or a binary
             encoding of 9 decimal digits per 4-byte big-endian
             integer
 * timestamp - little endian integer representing seconds relative to epoch (< 5.6)
 * timestamp2 - big-endian integer representing seconds relative to epoch (5.6+);
                additionally packed fractional digits, similar to the decimal format
 * date/time - encodes the various components into various bits of a 3 - 8 byte integer
 * char - just a string with ``length`` bytes (space padded)
 * varchar - length-prefix string, with the prefix being a little endian integer of
             1 to 2 bytes.

See dbsake/mysqlfrm/mysqltypes.py unpack_type_<name> method for how each datatype
is actually decoded.

Extra data section
~~~~~~~~~~~~~~~~~~

The "extra" section encodes some basic table properties.  These include:

 * CONNECTION=<name> string (used by FEDERATED)
 * ENGINE=<name> strings
 * PARTITION BY string
 * "auto partitioned flag" (used by NDB, at least)
 * WITH PARSER - fulltext parser plugin names
 * Table COMMENT '...' - only if > 254 bytes

Except for the fulltext parser plugin names (which are null terminated), all
of these properties are length-prefix strings.  This essentially has the format:

::

 [2-byte length][<connection string>]
 [2-byte length][<engine name string>]
 [4-byte length][<partition by clause>][null byte]
 [1-byte is_autopartitioned flag]
 [parser name][null_byte] for each fulltext parser plugin used
 [2-byte length][<table comment string>]

These strings should be decoded per the table's default character set.

FormInfo
~~~~~~~~

The .frm form info is a section consisting of 288 bytes with integers
noting the length or count of elements in the table.

The start of this section can be found at offset 64 + names_len from the
.frm header and the offset is a 4 byte integer.  In python this would
be found via

.. code-block:: python

   >> f = open('/var/lib/mysql/mysql/user.frm', 'rb')
   >> f.seek(0x0004) # "names_length" documented in the .frm fileinfo header
   >> names_len, = struct.unpack("<H", f.read(2)) # always 3 in modern mysql
   >> f.seek(64 + names_len)
   >> forminfo_offset, = struct.unpack("<I", f.read(4))

Here is a description of some of the more interesting fields available in
the forminfo section.  This is not meant to be exhaustive but merely to
document the fields necessary for interpreting pertinent column metadata.

All offsets are relative to the start of the forminfo section

column_count
    2 byte integer at offset 258

    The number of coumns defined on this table

screens_length
   2 byte integer at offset 260
 
   How many bytes follow the forminfo section prior to the start of the
   column metadata  

null_columns
    2 byte integer at offset 282

    How many nullable columns are defined in this table

names_length
    2 byte integer at offset 268

    Length in bytes (including delimiters) of column names

interval_length
    2 byte integer at offset 274

    Length in bytes (including delimiters) of the set/enum labels

comments_length
    2 byte integer at offset 284

    Length in bytes of the column comments


Column Metadata
~~~~~~~~~~~~~~~

17 bytes per column

Followed by \\xff separated column names

Followed by a null byte

Followed by null terminated interval groups with each interval group
consisting of interval names \\xff separated.

Followed by a single string of column comments.

