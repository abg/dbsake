.frm fileinfo section
---------------------

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
| 0033 | 51  | 4-bytes        | MYSQL_VERSION_ID                             |
+------+-----+                |                                              |
| 0034 | 52  |                |                                              |
+------+-----+                |                                              |
| 0035 | 53  |                |                                              |
+------+-----+                |                                              |
| 0036 | 54  |                |                                              |
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
----------------

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

Each index group consists of the index metadata and then metadata for each 
indexed column.  This has the format:

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
| offset       | 2 bytes | ???                                               |
+--------------+---------+---------------------------------------------------+
| unused       | 1 byte  |                                                   |
+--------------+---------+---------------------------------------------------+
| key_type     | 2 bytes | maps to enum ha_base_keytype                      |
+--------------+---------+---------------------------------------------------+
| length       | 2 bytes | length of this index component                    |
+--------------+---------+---------------------------------------------------+

After this metadata the index names follow.  This is a group of 0xff delimited
strings.  

Example:
    "\xffPRIMARY\xffidx_col1\xffidx_col2\xff"

After the column names is a set of column comments.

Defaults Section
----------------

This called the "record buffer" in MySQL

This data has the default values for all columns where a default is defined.

Effectively you can think of this data as "this is how you should instantiate
the field instance".

There are a leading series of 1 or more bytes that contains the "null map"
with 1 bit for every column that is potentially nullable - and if set
denotes the default value is NULL and there is no data for that column.

There is always at least 1 byte for the null map even if a table has no
nullable columns.

Otherwise the default data is encoded according to the data type and
the location in the defaults buffer can be found from the column metadata
"record_offset" attribute.

Extra info section
------------------

FormInfo
--------

Column Metadata
---------------


