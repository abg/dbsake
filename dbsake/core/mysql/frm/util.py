"""
dbsake.core.mysql.frm.util
~~~~~~~~~~~~~~~~~~~~~~~~~~

Utility methods

"""
import contextlib
import functools
import io
import os
import re
import struct


# Utility class for reading and interpreting packed byte strings
class ByteReader(io.BytesIO):

    @contextlib.contextmanager
    def offset(self, offset, whence=os.SEEK_SET):
        """Temporarily adjust the offset

        The original offset is restored at the end of the
        context manager

        Example:
        my_data = ByteReader(data)
        # read 2 bytes at offset 0x0010
        with my_data.offset(0x0010):
            field = my_data.read(2)
        my_data.tell() # restored to original offset
        """
        original_offset = self.tell()
        self.seek(offset, whence)
        yield
        self.seek(original_offset, os.SEEK_SET)

    def uint8(self):
        return struct.unpack('B', self.read(1))[0]

    def sint8(self):
        return struct.unpack('b', self.read(1))[0]

    def uint16(self, endian="<"):
        """Read next 16bit integer are the current offset"""
        if endian == '<':
            return struct.unpack('<H', self.read(2))[0]
        else:
            return struct.unpack('>H', self.read(2))[0]

    def sint16(self):
        return struct.unpack('<h', self.read(2))[0]

    def uint24(self, endian="<"):
        if endian == '<':
            return struct.unpack('<I', self.read(3) + b'\x00')[0]
        elif endian == '>':
            return struct.unpack('>I', b'\x00' + self.read(3))[0]
        else:
            raise ValueError("Bad endian value %r" % endian)

    def sint24(self, endian="<"):
        data = self.read(3)
        if endian == "<":
            msb, = struct.unpack("B", data[-1:])
        else:
            msb, = struct.unpack("B", data[0:1])
        # check high bit so we can extend sign appropriately
        if msb & 0x80:
            pad = b'\xff'
        else:
            pad = b'\x00'
        if endian == '<':
            return struct.unpack('<i', data + pad)[0]
        else:
            return struct.unpack('>i', pad + data)[0]

    def uint32(self, endian="<"):
        if endian == "<":
            return struct.unpack('<I', self.read(4))[0]
        elif endian == ">":
            return struct.unpack(">I", self.read(4))[0]

    def sint32(self, endian="<"):
        if endian == '<':
            return struct.unpack('<i', self.read(4))[0]
        elif endian == '>':
            return struct.unpack('>i', self.read(4))[0]
        else:
            raise ValueError("Bad endian value %r" % endian)

    def uint40(self, endian="<"):
        """Read an unsigned 5 byte integer"""
        if endian == '<':
            return struct.unpack('<Q', self.read(5) + b'\x00'*3)[0]
        elif endian == '>':
            return struct.unpack('>Q', b'\x00'*3 + self.read(5))[0]

    def uint48(self, endian="<"):
        if endian == "<":
            return struct.unpack('<Q', self.read(6) + b'\x00'*2)[0]
        elif endian == '>':
            return struct.unpack('>Q', b'\x00'*2 + self.read(6))[0]

    def uint64(self, endian="<"):
        assert endian in ("<", ">")
        return struct.unpack('%sQ' % endian, self.read(8))[0]

    def sint64(self):
        return struct.unpack('<q', self.read(8))[0]

    def float(self):
        return struct.unpack('<f', self.read(4))[0]

    def double(self):
        return struct.unpack('<d', self.read(8))[0]

    def bytes_prefix16(self):
        """Read a length-prefix string

        Reads a 16-bit integer length and
        return ``length`` bytes

        :returns: byte string
        """
        return self.read(self.uint16())

    def bytes_prefix32(self):
        return self.read(self.uint32())

    def bytes0(self):
        """Read a null terminated string

        :returns: byte string, without trailing null
        """
        # find the offset from the current position
        current_pos = self.tell()
        try:
            length = self.getvalue().index(b'\x00', current_pos) - current_pos
        except ValueError:
            return ''
        # read the next bytes, except for the trailing null
        try:
            return self.read(length)
        finally:
            # skip the trailing null
            self.skip(1)

    # Offset based methods
    # These read values at some offset and
    # restore the original offset.
    def uint8_at(self, offset, whence=os.SEEK_SET):
        with self.offset(offset, whence):
            return self.uint8()

    def sint8_at(self, offset, whence=os.SEEK_SET):
        with self.offset(offset, whence):
            return self.sint8()

    def uint16_at(self, offset, whence=os.SEEK_SET):
        with self.offset(offset, whence):
            return self.uint16()

    def sint16_at(self, offset, whence=os.SEEK_SET):
        with self.offset(offset, whence):
            return self.sint16()

    def uint24_at(self, offset, whence=os.SEEK_SET):
        with self.offset(offset, whence):
            return self.uint24()

    def sint24_at(self, offset, whence=os.SEEK_SET):
        with self.offset(offset, whence):
            return self.sint24()

    def uint32_at(self, offset, whence=os.SEEK_SET):
        with self.offset(offset, whence):
            return self.uint32()

    def sint32_at(self, offset, whence=os.SEEK_SET):
        with self.offset(offset, whence):
            return self.sint32()

    def uint64_at(self, offset, whence=os.SEEK_SET):
        with self.offset(offset, whence):
            return self.uint64()

    def sint64_at(self, offset, whence=os.SEEK_SET):
        with self.offset(offset, whence):
            return self.sint64()

    def read_at(self, size, offset, whence=os.SEEK_SET):
        with self.offset(offset, whence):
            return self.read(size)

    # Skip support to move the cursor forward
    # Convenience method wrapping BytesIO.seek(offset, whence)
    def skip(self, n_bytes):
        self.seek(n_bytes, os.SEEK_CUR)


# py2/py3 compatibility shim
# Taken from https://bitbucket.org/gutworth/six
def add_metaclass(metaclass):
    """Class decorator for creating a class with a metaclass."""
    @functools.wraps(metaclass)
    def wrapper(cls):
        """Instantiate cls with the provided metaclass"""
        orig_vars = cls.__dict__.copy()
        orig_vars.pop('__dict__', None)
        orig_vars.pop('__weakref__', None)
        for slots_var in orig_vars.get('__slots__', ()):
            orig_vars.pop(slots_var)
        return metaclass(cls.__name__, cls.__bases__, orig_vars)
    return wrapper


# Suppress pylint's "Too few methods" warning
# pylint: disable=R0903
class BitFlagDescriptor(object):
    """Descriptor representing a bit flag

    The descriptor should be initialized with a power of 2
    indicating some flag value.

    The instance associated with this BitFlag must evaluate to
    an integer.

    This descriptor is intended to work with the BitFlags implementation.

    When this descriptor is accessed as a class level attribute it returns
    the bit value.   When accessed as an instance attribute it returns a
    boolean True if the attached instance has the bit value set, or False
    otherwise.
    """

    def __init__(self, value):
        self.value = value

    def __get__(self, instance, cls):
        if instance is None:
            return self.value
        else:
            return bool(instance.value & self.value)

    def __set__(self, instance, value):
        if instance is None:
            raise ValueError("Class level bitflags are immutable")
        if value:
            instance.value |= self.value
        else:
            instance.value &= ~self.value

    def __delete__(self, instance):
        instance.value &= ~self.value

    def __index__(self):
        return self.value

    __int__ = __index__


class BitFlagsMeta(type):
    """Metaclass for BitFlags

    This metaclass wraps all class level integer attributes and
    wraps them in a BitFlagDescriptor.  Additionally a _members_
    attribute is added to the underlying class containing a list
    of flags name, sorted by the flag value.
    """

    def __new__(mcs, name, bases, classdict):
        # convert class members to BitFlags
        # and track the order of members by value
        members = []
        for key, value in classdict.items():
            if key.startswith('_'):
                continue
            # skip members that are not an integer
            try:
                int(value)
            except (TypeError, ValueError):
                continue
            classdict[key] = BitFlagDescriptor(value)
            members.append(key)
        classdict['_members_'] = members
        return super(BitFlagsMeta, mcs).__new__(mcs, name, bases, classdict)


@add_metaclass(BitFlagsMeta)
class BitFlags(object):
    """Container for an integer representing bit flags"""

    _members_ = ()

    def __init__(self, value=0):
        self.value = value

    def __index__(self):
        return self.value

    __int__ = __index__

    def enable(self, *names):
        """Enable a set of bit flags by name"""
        for name in names:
            if name not in self._members_:
                raise ValueError("Invalid flag name '{0}'".format(name))
            setattr(self, name, True)
        return self

    def disable(self, *names):
        """Disable a set of bit flags by name"""
        for name in names:
            if name not in self._members_:
                raise ValueError("Invalid flag name '{0}'".format(name))
            setattr(self, name, False)
        return self

    def clear(self):
        """Clear all bit flags"""
        self.value = 0
        return self

    def __repr__(self):
        attrs = []
        for name in self._members_:
            if getattr(self, name):
                attrs.append(repr(name))
        return '{classname}({attrs})'.format(classname=self.__class__.__name__,
                                             attrs=','.join(attrs))


def unescape(value):
    """Remove backslash escapes from a string

    :returns: unescaped string
    """
    meta_mapping = {
        'b': "\b",
        't': "\t",
        'n': "\n",
        'r': "\r",
        '\\': "\\",
        's': " ",
        '"': '"',
        "'": "'"
    }

    def replace(match):
        return meta_mapping[match.group(1)]

    regex = re.compile(r'''\\(['"btnr\\s])''')
    return regex.sub(replace, value)
