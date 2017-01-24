"""
dbsake.core.mysqlfrm.constants
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Constants used during .frm parsing
"""
from dbsake.util import enum

from . import util


# enum legacy_db_type
# {
#  DB_TYPE_UNKNOWN=0,DB_TYPE_DIAB_ISAM=1,
#  DB_TYPE_HASH,DB_TYPE_MISAM,DB_TYPE_PISAM,
#  DB_TYPE_RMS_ISAM, DB_TYPE_HEAP, DB_TYPE_ISAM,
#  DB_TYPE_MRG_ISAM, DB_TYPE_MYISAM, DB_TYPE_MRG_MYISAM,
#  DB_TYPE_BERKELEY_DB, DB_TYPE_INNODB,
#  DB_TYPE_GEMINI, DB_TYPE_NDBCLUSTER,
#  DB_TYPE_EXAMPLE_DB, DB_TYPE_ARCHIVE_DB, DB_TYPE_CSV_DB,
#  DB_TYPE_FEDERATED_DB,
#  DB_TYPE_BLACKHOLE_DB,
#  DB_TYPE_PARTITION_DB,
#  DB_TYPE_BINLOG,
#  DB_TYPE_SOLID,
#  DB_TYPE_PBXT,
#  DB_TYPE_TABLE_FUNCTION,
#  DB_TYPE_MEMCACHE,
#  DB_TYPE_FALCON,
#  DB_TYPE_MARIA,
#  /** Performance schema engine. */
#  DB_TYPE_PERFORMANCE_SCHEMA,
#  DB_TYPE_FIRST_DYNAMIC=42,
#  DB_TYPE_DEFAULT=127 // Must be last
# };
class LegacyDBType(enum.IntEnum):
    UNKNOWN = 0
    DIAB_ISAM = 1
    HASH = 2
    MISAM = 3
    PISAM = 4
    RMS_ISAM = 5
    HEAP = 6
    ISAM = 7
    MRG_ISAM = 8
    MyISAM = 9
    MRG_MYISAM = 10
    BERKELEYDB = 11
    InnoDB = 12
    GEMINI = 13
    NDBCLUSTER = 14
    EXAMPLE_DB = 15
    ARCHIVE_DB = 16
    CSV = 17
    FEDERATED = 18
    BLACKHOLE = 19
    PARTITION_DB = 20
    BINLOG = 21
    SOLID = 22
    PBXT = 23
    TABLE_FUNCTION = 24
    MEMCACHE = 25
    FALCON = 26
    MARIA = 27
    PERFORMANCE_SCHEMA = 28
    FIRST_DYNAMIC = 42
    DEFAULT = 127


# from sql/sql_const.h
MAX_DATE_WIDTH = 10
MAX_TIME_WIDTH = 10
MAX_TIME_FULL_WIDTH = 23
MAX_DATETIME_WIDTH = 19


class FieldFlag(util.BitFlags):
    DECIMAL = 1
    BINARY = 1
    NUMBER = 2
    ZEROFILL = 4
    PACK = 120
    INTERVAL = 256
    BITFIELD = 512
    BLOB = 1024
    GEOM = 2048
    TREAT_BIT_AS_CHAR = 4096
    # defined, but not used in modern MySQL
    # LEFT_FULLSCREEN = 8192
    NO_DEFAULT = 16384
    # defined, but not used in modern MySQL
    # FORMAT_NUMBER = 16384
    # defined, but not used in modern MySQL
    # RIGHT_FULLSCREEN = 16385
    # defined, but not used in modern MySQL
    # SUM = 32768
    MAYBE_NULL = 32768
    HEX_ESCAPE = 0X10000
    PACK_SHIFT = 3
    DEC_SHIFT = 8
    MAX_DEC = 31
    NUM_SCREEN_TYPE = 0X7F01
    ALFA_SCREEN_TYPE = 0X7800


# Unireg types constants
# sql/field.h unireg constants
# enum utype  { NONE,DATE,SHIELD,NOEMPTY,CASEUP,PNR,BGNR,PGNR,YES,NO,REL,
#               CHECK,EMPTY,UNKNOWN_FIELD,CASEDN,NEXT_NUMBER,INTERVAL_FIELD,
#               BIT_FIELD, TIMESTAMP_OLD_FIELD, CAPITALIZE, BLOB_FIELD,
#               TIMESTAMP_DN_FIELD, TIMESTAMP_UN_FIELD, TIMESTAMP_DNUN_FIELD };

# Here we only explicitly define the values we use in this parsing
# Some notes here:
#  unireg_check = NONE may be set to disable the typical
#  "DEFAULT CURRENT_TIMESTAMP" behavior for datetimes
# NEXT_NUMBER flags the column as AUTO_INCREMENT
# TIMESTAMP_DN_FIELD means:
#   DEFAULT CURRENT_TIMESTAMP
# TIMESTAMP_UN_FIELD means:
#   DEFAULT <default value> ON UPDATE CURRENT_TIMESTAMP
# TIMESTAMP_DNUN_FIELD means:
#   DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
class Utype(enum.IntEnum):
    NONE = 0
    DATE = 1
    SHIELD = 2
    NOEMPTY = 3
    CASEUP = 4
    PNR = 5
    BGNR = 6
    PGNR = 7
    YES = 8
    NO = 9
    REL = 10
    CHECK = 11
    EMPTY = 12
    UNKNOWN_FIELD = 13
    CASEDN = 14
    NEXT_NUMBER = 15
    INTERVAL_FIELD = 16
    BIT_FIELD = 17
    TIMESTAMP_OLD_FIELD = 18
    CAPITALIZE = 19
    BLOB_FIELD = 20
    TIMESTAMP_DN_FIELD = 21
    TIMESTAMP_UN_FIELD = 22
    TIMESTAMP_DNUN_FIELD = 23


# include/mysql_com.h
# enum enum_field_types { ... };
class MySQLType(enum.IntEnum):
    DECIMAL = 0
    TINY = 1
    SHORT = 2
    LONG = 3
    FLOAT = 4
    DOUBLE = 5
    NULL = 6
    TIMESTAMP = 7
    LONGLONG = 8
    INT24 = 9
    DATE = 10
    TIME = 11
    DATETIME = 12
    YEAR = 13
    NEWDATE = 14
    VARCHAR = 15
    BIT = 16
    TIMESTAMP2 = 17
    DATETIME2 = 18
    TIME2 = 19
    NEWDECIMAL = 246
    ENUM = 247
    SET = 248
    TINY_BLOB = 249
    MEDIUM_BLOB = 250
    LONG_BLOB = 251
    BLOB = 252
    VAR_STRING = 253
    STRING = 254
    GEOMETRY = 255


#  enum geometry_type
#  {
#    GEOM_GEOMETRY = 0, GEOM_POINT = 1, GEOM_LINESTRING = 2, GEOM_POLYGON = 3,
#    GEOM_MULTIPOINT = 4, GEOM_MULTILINESTRING = 5, GEOM_MULTIPOLYGON = 6,
#    GEOM_GEOMETRYCOLLECTION = 7
#  };
class GeometryType(enum.IntEnum):
    GEOMETRY = 0
    POINT = 1
    LINESTRING = 2
    POLYGON = 3
    MULTIPOINT = 4
    MULTILINESTRING = 5
    MULTIPOLYGON = 6
    GEOMETRYCOLLECTION = 7


# HA_OPTION flags from include/my_base.h
# these map to flags in the 16 bit "table_options"
# at offset 0x001e in the .frm header
class HaOption(util.BitFlags):
    PACK_RECORD = 1
    PACK_KEYS = 2
    COMPRESS_RECORD = 4
    LONG_BLOB_PTR = 8     # /* new ISAM format */
    TMP_TABLE = 16
    CHECKSUM = 32
    DELAY_KEY_WRITE = 64
    NO_PACK_KEYS = 128   # /* Reserved for MySQL */
    CREATE_FROM_ENGINE = 256
    RELIES_ON_SQL_LAYER = 512
    NULL_FIELDS = 1024
    PAGE_CHECKSUM = 2048
    # /** STATS_PERSISTENT=1 has been specified in the SQL command (either
    #  CREATE or ALTER TABLE). Table and index statistics that are collected by
    # the storage engine and used by the optimizer for query optimization will
    # be stored on disk and will not change after a server restart. */
    STATS_PERSISTENT = 4096
    # /** STATS_PERSISTENT=0 has been specified in CREATE/ALTER TABLE.
    #     Statistics for the table will be wiped away on server shutdown and
    #     new ones recalculated after the server is started again. If none of
    #     HA_OPTION_STATS_PERSISTENT or HA_OPTION_NO_STATS_PERSISTENT is set,
    #     this means that the setting is not explicitly set at table level and
    #     the corresponding table will use whatever is the global server
    #     default. */
    NO_STATS_PERSISTENT = 8192
    TEMP_COMPRESS_RECORD = 16384  # /* set by isamchk */
    READ_ONLY_DATA = 32768  # /* Set by isamchk */


# const char *ha_row_type[] = {
#  "", "FIXED", "DYNAMIC", "COMPRESSED", "REDUNDANT", "COMPACT",
#  /* Reserved to be "PAGE" in future versions */ "?",
#  "?","?","?"
# };
class HaRowType(enum.Enum):
    DEFAULT = 0
    FIXED = 1
    DYNAMIC = 2
    COMPRESSED = 3
    REDUNDANT = 4
    COMPACT = 5
    UNKNOWN_6 = 6
    TOKUDB_UNCOMPRESSED = 7
    TOKUDB_ZLIB = 8
    TOKUDB_SNAPPY = 9
    TOKUDB_QUICKLZ = 10
    TOKUDB_LZMA = 11
    TOKUDB_FAST = 12
    TOKUDB_SMALL = 13
    TOKUDB_DEFAULT = 14
    UNKNOWN_15 = 15
    UNKNOWN_16 = 16
    UNKNOWN_17 = 17
    UNKNOWN_18 = 18

    @property
    def name(self):
        orig_name = super(HaRowType, self).name

        if orig_name == 'TOKUDB_DEFAULT':
            return 'TOKUDB_ZLIB'
        elif orig_name == 'TOKUDB_FAST':
            return 'TOKUDB_QUICKLZ'
        elif orig_name == 'TOKUDB_SMALL':
            return 'TOKUDB_LZMA'
        else:
            return orig_name

