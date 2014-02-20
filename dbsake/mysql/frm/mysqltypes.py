"""
dbsake.mysql.frm.mysqltypes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Support for formatting and decoding MySQL types

format_type_* methods convert MySQL "field" data into a human readable
SQL type (e.g. MYSQL_TYPE_STRING -> CHAR(255) NOT NULL)

unpack_type_* methods decode the default values for a column for
display in a show create table "DEFAULT ..." clause.
(e.g. \\x2a\\x00\\x00\\x00 -> DEFAULT '42')
"""

import datetime
import sys

# local imports
from . import constants
from . import charsets

## Formatting of types
def format_type(context):
    name = context.type_code.name.lower()
    try:
        dispatch = globals()['format_type_{0}'.format(name)]
    except KeyError:
        raise LookupError("No method to format type {0}".format(context.type_code))

    result = dispatch(context)

    if not context.flags.MAYBE_NULL:
        result += ' NOT NULL'

    if context.unireg_check.name == 'NEXT_NUMBER':
        result += ' AUTO_INCREMENT'

    return result

def _format_number(name, context):
    value = name
    if context.length:
        value += '({0})'.format(context.length)
    if not context.flags.DECIMAL:
        value += ' unsigned'
    if context.flags.ZEROFILL:
        value += ' zerofill'
    return value


def format_type_tiny(context):
    return _format_number('tinyint', context)

def format_type_short(context):
    return _format_number('smallint', context)

def format_type_int24(context):
    return _format_number('mediumint', context)

def format_type_long(context):
    return _format_number('int', context)

def format_type_longlong(context):
    return _format_number('bigint', context)

def format_type_newdecimal(context):
    precision = context.length
    scale = (int(context.flags) >> 8) & 31
    if scale:
        precision -= 1
    if precision:
        precision -= 1

    return "decimal({0},{1})".format(precision, scale)

# old <5.0 decimal format is formatted the same way
# scale and precision are taken from pack length
# and pack flags accordingly
format_type_decimal = format_type_newdecimal

def _format_real(name, context):
    if context.flags.DECIMAL:
        precision = context.length
        scale = (int(context.flags) >> 8) & 31
        # if scale is way out of range, this probably means
        # we shouldn't format the <type>(M,D) syntax 
        if scale > 30:
            value = name
        else:
            value = '{0}({1},{2})'.format(name, precision, scale)
    else:
        value = name + ' unsigned'

    if context.flags.ZEROFILL:
        value += ' zerofill'

    return value

def format_type_float(context):
    return _format_real('float', context)

def format_type_double(context):
    return _format_real('double', context)

## String types
def _format_charset(context):
    value = ''
    if context.table.charset != context.charset:
        value += ' CHARACTER SET {0}'.format(context.charset.name)
    if not context.charset.is_default:
        value += ' COLLATE {0}'.format(context.charset.collation)
    return value

def format_type_string(context):
    value = 'char({0})'.format(context.length // context.charset.maxlen)
    return value + _format_charset(context)

def format_type_varchar(context):
    value = 'varchar({0})'.format(context.length // context.charset.maxlen)
    return value + _format_charset(context)

# var_string should be identical to varchar here
# but is an older datatype from MySQL 4.1
format_type_var_string = format_type_varchar

## Enum type
def format_type_enum(context):
    value = 'enum({0})'.format(','.join("'%s'" % name
                                        for name in context.labels))
    return value + _format_charset(context)

## SET type
def format_type_set(context):
    value = 'set({0})'.format(','.join("'%s'" % name
                                       for name in context.labels))
    return value + _format_charset(context)

## Blob typesa
def format_type_tiny_blob(context):
    if context.charset.name == 'binary':
        return 'tinyblob'
    else:
        return 'tinytext'

def format_type_blob(context):
    if context.charset.name == 'binary':
        return 'blob'
    else:
        return 'text'

def format_type_medium_blob(context):
    if context.charset.name == 'binary':
        return 'mediumblob'
    else:
        return 'mediumtext'

def format_type_long_blob(context):
    if context.charset.name == 'binary':
        return 'longblob'
    else:
        return 'longtext'

def format_type_bit(context):
    return 'bit({0})'.format(context.length)

def format_type_time2(context):
    scale = context.length - constants.MAX_TIME_WIDTH - 1
    if scale > 0:
        return 'time({0})'.format(scale)
    else:
        return 'time'
format_type_time = format_type_time2

def format_type_timestamp2(context):
    scale = context.length - constants.MAX_DATETIME_WIDTH - 1
    if scale > 0:
        return 'timestamp({0})'.format(scale)
    else:
        return 'timestamp'
format_type_timestamp = format_type_timestamp2

def format_type_year(context):
    return 'year({0})'.format(context.length)

def format_type_newdate(context):
    return 'date'
format_type_date = format_type_newdate

def format_type_datetime2(context):
    scale = context.length - constants.MAX_DATETIME_WIDTH - 1
    if scale > 0:
        return 'datetime({0})'.format(scale)
    else:
        return 'datetime'
format_type_datetime = format_type_datetime2

def format_type_geometry(context):
    return context.subtype_code.name.lower()

## Defaults unpacking
def unpack_default(defaults, context):
    """Unpack a default value from the defaults ("record") buffer

    :param defaults: util.ByteReader instance offset at the current
                     record offset.
    :param context: A dict instance with context information for the
                    current column being unpacked. At a minimum we
                    expect members of:
                        type_code - a MySQLType enum instance
                        flags - BitFlags instance with field flags
                        null_bit - current null bit offset pointing to
                                   the current columns bit position (if nullable)
                        null_map - bit string of nullable column bits
    :returns: string of default value
    """
    # Utype.NEXT_NUMBER (AUTO_INCREMENT) columns will never have a default
    # blob fields also never have a default in any current MySQL version but
    # some mysql forks don't set the NO_DEFAULT field flag, so default
    # processing is special cased here to handle these cases
    if (context.flags.NO_DEFAULT or
        context.unireg_check == constants.Utype.NEXT_NUMBER):
        return None

    if context.flags.MAYBE_NULL:
        null_map = context.null_map
        offset = context.null_bit // 8
        null_byte = null_map[context.null_bit // 8]
        null_bit = context.null_bit % 8
        context.null_bit += 1
        if null_byte & (1 << null_bit) and \
                not context.unireg_check == constants.Utype.BLOB_FIELD:
            return 'NULL'

    if context.unireg_check == constants.Utype.BLOB_FIELD:
        # suppress default for blob types
        return None
    
    type_name = context.type_code.name.lower()
    try:
        dispatch = globals()['unpack_type_{0}'.format(type_name)]
    except KeyError:
        raise LookupError("No method to decode default for type {0}".format(context.type_code))
    else:
        try:
            return dispatch(defaults, context)
        except NotImplementedError:
            raise LookupError("Unpack method not implemented for {0!r}".format(context.type_code))

## Decimal (exact precision) types
def unpack_type_decimal(defaults, context):
    return "'{0}'".format(defaults.read(context.length).decode('ascii'))

import operator
import struct

DIG_PER_DEC1 = 9
DIGITS_TO_BYTES = [ 0, 1, 1, 2, 2, 3, 3, 4, 4, 4 ]


def  _decode_decimal(data, invert=False):
    """Decode the decimal digits from a set of bytes

    This does not zero pad fractional digits - so these
    may need to be zerofilled or otherwise shifted. Only
    the raw decimal number string represented by the bytes
    will be returned without leading zeros.

    This is intended to decode MySQL's scheme of encoding
    up to 9 decimal digits into a 4 byte word for its
    fixed precision DECIMAL type.

    return string of decimal numbers

    Examples:
         b'\x01' -> '1'
         b'\x63' -> '99'
         b'\x3b\x9a\xc9\xff' -> '999999999'
    """
    if len(data) % 4:
        pad = 4 - len(data) % 4
        pad_char = b'\xff' if invert else b'\x00'
        data = pad_char*pad + data
    groups = struct.unpack('>' + 'i'*(len(data) // 4), data)
    if invert:
        groups = map(operator.invert, groups)
    return ''.join(str(i) for i in groups)

def unpack_type_newdecimal(defaults, context):
    """Unpack a MySQL 5.0+ NEWDECIMAL value

    MySQL 5.0 packs decimal values into groups of 9 decimal digits
    per 4 byte word. The first byte encodes the sign bit as the
    most significant bit.  The first byte is always xor'd with
    0x80.

    """
    precision = context.length
    scale = (int(context.flags) >> 8) & 31
    if scale:
        precision -= 1
    if precision:
        precision -= 1

    int_length = ((precision - scale) // 9)*4 + \
                 DIGITS_TO_BYTES[(precision - scale) % 9]
    frac_length = (scale // 9)*4 + DIGITS_TO_BYTES[scale % 9]
    data = defaults.read(int_length + frac_length)

    first, = struct.unpack_from('B', data, 0)
    sign = '' if first & 0x80 else '-'
    data = struct.pack('B', first ^ 0x80) + data[1:]
    parts = []

    if int_length:
        integer_part = _decode_decimal(data[0:int_length],
                                       invert=bool(sign))
        parts.append(sign + integer_part)
    else:
        parts.append(sign + '0')

    if frac_length:
        fractional_part = _decode_decimal(data[-frac_length:],
                                          invert=bool(sign))
        parts.append(str(fractional_part).zfill(scale))

    return "%r" % '.'.join(parts)

## Integer types
# For integer types signed is denoted
# by tagging the FIELDFLAG_DECIMAL flag
def _format_integer_default(value):
    return "'%d'" % value

def unpack_type_tiny(defaults, context):
    """Unpack a MySQL TINY 1-byte integer"""
    value = defaults.sint8() if context.flags.DECIMAL else defaults.uint8()
    return _format_integer_default(value)

def unpack_type_short(defaults, context):
    value = defaults.sint16() if context.flags.DECIMAL else defaults.uint16()
    return _format_integer_default(value)

def unpack_type_int24(defaults, context):
    value = defaults.sint24() if context.flags.DECIMAL else defaults.uint24()
    return _format_integer_default(value)

def unpack_type_long(defaults, context):
    value = defaults.sint32() if context.flags.DECIMAL else defaults.uint32()
    return _format_integer_default(value)

def unpack_type_longlong(defaults, context):
    value = defaults.sint64() if context.flags.DECIMAL else defaults.uint64()
    return _format_integer_default(value)

## Floating point types
def unpack_type_float(defaults, context):
    return "'%s'" % str(defaults.float()).rstrip('0')

def unpack_type_double(defaults, context):
    return "'%s'" % str(defaults.double()).rstrip('0')

## Null type
def unpack_type_null(defaults, context):
    return None


## Date/Time types
def unpack_type_time(defaults, context):
    value = defaults.uint24()
    hour = value // 10000
    minute = (value // 100) % 100
    second = value % 100
    return "'%s'" % '{hour}:{minute}:{second}'.format(hour=hour,
                                                      minute=minute,
                                                      second=second)

def unpack_type_time2(defaults, context):
    data = defaults.read(3)
    first, = struct.unpack_from('B', data, 0)
    is_neg = not first & 0x80
    data = b'\x00' + struct.pack('b', first - 0x80) + data[1:]
    value, = struct.unpack('>i', data)
    if is_neg:
        value = ~value
    hour = (value >> 12) % (1 << 10)
    minute = (value >> 6) % (1 << 6)
    second = value % (1 << 6)
    result = '{0}:{1}:{2}'.format(hour, minute, second)

    scale = context.length - constants.MAX_TIME_WIDTH - 1

    if scale > 0:
        data = defaults.read(DIGITS_TO_BYTES[scale])
        if len(data) % 4:
            pad = 4 - len(data) % 4
            pad_char = b'\xff' if is_neg else b'\x00'
            data = pad_char*pad + data
        frac_part, = struct.unpack('>i', data)
        if frac_part < 0:
            frac_part = -frac_part
        result += '.' + str(frac_part).zfill(scale)

    if is_neg:
        result = '-' + result
    return "'{0}'".format(result)

def unpack_type_year(defaults, context):
    value = defaults.uint8()
    if value == 0:
        return "'0000'"
    else:
        return "'{0}'".format(1900 + value)

# pre 4.1 - unsupported for now, should be rare
def unpack_type_date(defaults, context):
    raise NotImplementedError

def unpack_type_newdate(defaults, context):
    # 3 bytes, big endian packed
    value = defaults.uint24()
    year = value >> 9
    month = (value >> 5) & 15
    day = value & 31
    return "'{0:4}-{1:02}-{2:02}'".format(year, month, day)

# XXX: Handle mariadb timestamp(N) columns
#      stored as MYSQL_TYPE_TIMESTAMP values
def unpack_type_timestamp(defaults, context):
    fmt = '%Y-%m-%d %H:%M:%S'
    epoch = defaults.sint32(endian="<")
    value = datetime.datetime.fromtimestamp(epoch).strftime(fmt)
    if context.unireg_check.name == 'TIMESTAMP_DN_FIELD':
        return 'CURRENT_TIMESTAMP'
    elif context.unireg_check.name == 'TIMESTAMP_UN_FIELD':
        return "'{0}' ON UPDATE CURRENT_TIMESTAMP".format(value)
    elif context.unireg_check.name == 'TIMESTAMP_DNUN_FIELD':
        return 'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'
    else:
        return "'{0}'".format(value)

def unpack_type_timestamp2(defaults, context):
    fmt = '%Y-%m-%d %H:%M:%S'
    epoch = defaults.sint32(endian=">")
    value = datetime.datetime.fromtimestamp(epoch).strftime(fmt)
    scale = context.length - constants.MAX_DATETIME_WIDTH - 1
    if scale > 0:
        nbytes = DIGITS_TO_BYTES[scale]
        if nbytes == 1:
            fractional = defaults.uint8(">")
        elif nbytes == 2:
            fractional = defaults.uint16(">")
        elif nbytes == 3:
            fractional = defaults.uint24(">")
        else:
            raise ValueError("Invalid scale for TIMESTAMP(%r)" % scale)
        value += '.' + str(fractional).zfill(scale)

    scale_str = '(%d)' % scale if scale > 0 else ''
    if context.unireg_check.name == 'TIMESTAMP_DN_FIELD':
        return 'CURRENT_TIMESTAMP{0}'.format(scale_str)
    elif context.unireg_check.name == 'TIMESTAMP_UN_FIELD':
        return "'{0}' ON UPDATE CURRENT_TIMESTAMP{1}".format(value, scale_str)
    elif context.unireg_check.name == 'TIMESTAMP_DNUN_FIELD':
        return 'CURRENT_TIMESTAMP{0} ON UPDATE CURRENT_TIMESTAMP{0}'.format(scale_str)
    else:
        return "'{0}'".format(value)

def unpack_type_datetime(defaults, context):
    value = defaults.uint64()
    # map field to # of encoded digits
    units = (
        ('second', 2),
        ('minute', 2),
        ('hour', 2),
        ('day', 2),
        ('month', 2),
        ('year', 4)
    )
    kwargs = {}
    for name, digits in units:
        unit_value = value % 10**digits
        value //= 10**digits
        kwargs[name] = str(unit_value).zfill(digits)
    return "'{year}-{month}-{day} {hour}:{minute}:{second}'".format(**kwargs)

def unpack_type_datetime2(defaults, context):
    ymdhms = defaults.uint40(endian=">")
    ymd = ymdhms >> 17
    ym = (ymd >> 5) & ~(2**17)
    day = ymd % (1 << 5)
    month = ym % 13
    year = ym // 13
    hms = ymdhms % (1 << 17)
    second = hms % (1 << 6)
    minute = (hms >> 6) % (1 << 6)
    hour = hms >> 12
    microseconds = 0

    value = '{0}-{1:02}-{2:02} {3:02}:{4:02}:{5:02}'.format(year,
                                                            month,
                                                            day,
                                                            hour,
                                                            minute,
                                                            second)
    scale = context.length - constants.MAX_DATETIME_WIDTH - 1
    if scale > 0:
        frac_bytes = defaults.read(DIGITS_TO_BYTES[scale])
        microseconds, = struct.unpack('>I', b'\x00'*(4 - len(frac_bytes)) + frac_bytes)
        value += '.' + str(microseconds).rstrip('0').zfill(scale)
    return "'{0}'".format(value)


## String types
def unpack_type_varchar(defaults, context):
    if context.length < 256:
        length = defaults.uint8()
    else:
        length = defaults.uint16()
    return "%r" % defaults.read(length)

# This is the 4.1 varchar type, but with trailing whitespace
# that pads up to VARCHAR(N) bytes
# e.g. VARCHAR(5) default 'a' -> 'a    ' in 4.1
# so we use the same logic as unpack_type_varchar, but then
# strip the trailing whitespace
def unpack_type_var_string(defaults, context):
    if context.length < 256:
        length = defaults.uint8()
    else:
        length = defaults.uint16()
    return "'%s'" % defaults.read(length).rstrip(' ').encode("string_escape")

def unpack_type_string(defaults, context):
    """Unpack a CHAR(N) fixed length string"""
    # Trailing spaces are always stripped for CHAR fields
    return "%r" % defaults.read(context.length).rstrip(' ')

## MySQL BIT(m) type
def unpack_type_bit(defaults, context):
    nbytes = (context.length + 7) // 8
    pad = b'\x00'*(8 - nbytes)
    value, = struct.unpack('>Q', pad + defaults.read(nbytes))
    return "b'{0}'".format(bin(value)[2:])

## MySQL ENUM TYPE
def unpack_type_enum(defaults, context):
    labels = context.labels
    if len(labels) < 256:
        offset = defaults.uint8() - 1
    else:
        offset = defaults.uint16() - 1

    try:
        return "'%s'" % labels[offset]
    except IndexError:
        return "''"

## MySQL SET Type
def unpack_type_set(defaults, context):
    elt_count = len(context.labels)
    n_bytes = (elt_count + 7) // 8
    if n_bytes > 4:
        n_bytes = 8
 
    if n_bytes == 1:
        value = defaults.uint8()
    elif n_bytes == 2:
        value = defaults.uint16()
    elif n_bytes == 3:
        value = defaults.uint24()
    elif n_bytes == 4:
        value = defaults.uint32()
    elif n_bytes == 8:
        value = defaults.uint64()
    else:
        raise ValueError("Sets cannot have more than 64 elements!")
    result = []
    for bit, name in enumerate(context.labels):
        if value & (1 << bit):
            result.append(name)
    return "'%s'" % ','.join(result)

## These following handlers are left unimplemented - they cannot have default
##  values in any current MySQL version.
## included here for documentation purposes
## MySQL BLOB/TEXT types
def unpack_type_long_blob(defaults, context):
    print "Weird - no NO_DEFAULT flag for blob (name=%r flags=%r)" % (context.name, context.flags)
    return None
unpack_type_tiny_blob = unpack_type_long_blob
unpack_type_medium_blob = unpack_type_long_blob
unpack_type_blob = unpack_type_long_blob

## MySQL GEOMETRY type
def unpack_type_geometry(defaults, context):
    raise NotImplementedError
