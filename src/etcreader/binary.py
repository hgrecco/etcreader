"""
    etcreader.binary
    ~~~~~~~~~~~~~~~~

    Read PicoQuant EasyTau files (etc extension).

    This is adapted from bytechomp

    :copyright: 2024 by etcreader Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import struct
from typing import (
    Annotated,
    Any,
    NewType,
    TypedDict,
    _TypedDictMeta,  # type: ignore
    get_args,
    get_origin,
    get_type_hints,
)

from typing_extensions import Buffer

#################
# Primary types
#################

PAD = NewType("PAD", int)
BOOL = NewType("BOOL", bool)
CHAR = NewType("CHAR", bytes)
CHAR_ARRAY = NewType("CHAR_ARRAY", bytes)
U8 = NewType("U8", int)
U16 = NewType("U16", int)
U32 = NewType("U32", int)
U64 = NewType("U64", int)
I8 = NewType("I8", int)
I16 = NewType("I16", int)
I32 = NewType("I32", int)
I64 = NewType("I64", int)
F16 = NewType("F16", float)
F32 = NewType("F32", float)
F64 = NewType("F64", float)

type PrimaryTypes = PAD | BOOL | CHAR | U8 | U16 | U32 | U64 | I8 | I16 | I32 | I64 | F16 | F32 | F64 | CHAR_ARRAY

_PrimaryTypesList = get_args(PrimaryTypes.__value__)


#########################
# Base TypedDict classes
#########################

class NativeSize(TypedDict):
    """Native byte order, size, and alignment
    """

class Native(TypedDict):
    """Native byte order, standard size, and no alignment
    """

class LittleEndian(TypedDict):
    """Little-endian byte order, standard size, and no alignment
    """

class BigEndian(TypedDict):
    """Big-endian byte order, standard size, and no alignment
    """

class Network(TypedDict):
    """Network (big-endian) byte order, standard size, and no alignment
    """

type ByteOrderSizeAlignment = NativeSize | Native | LittleEndian | BigEndian | Network

###################
# Helper function
###################

def is_typed_dict(cls: type) -> bool:
    """Return whether 'cls' is derived from TypedDict.
    """
    return isinstance(cls, _TypedDictMeta)

def is_typed_dict_of(cls: type, base: type) -> bool:
    """Return whether 'cls' is derived from base typed dict.
    """
    if not is_typed_dict(cls):
        return False
    try:
        return base in cls.__orig_bases__ # type: ignore
    except AttributeError:
        return False

def get_byte_order(cls: type, default: str="=") -> str:
    """Return byte order, size and alignment character for a given cls TypeDict.

    Return `default` if cls is not in known base classes.
    """
    if is_typed_dict_of(cls, NativeSize):
        return "@"
    elif is_typed_dict_of(cls, Native):
        return "="
    elif is_typed_dict_of(cls, LittleEndian):
        return "<"
    elif is_typed_dict_of(cls, BigEndian):
        return ">"
    elif is_typed_dict_of(cls, Network):
        return "!"
    return default


def build_format(primary_type: type[PrimaryTypes], byte_order: str, length: int=1) -> str:
    """Build a struct compact format string.
    """
    if primary_type is PAD:
        return byte_order + "x" * length 
    elif primary_type is BOOL:
        return byte_order + "?" * length 
    elif primary_type is U8:
        return byte_order + "B" * length
    elif primary_type is U16:    
        return byte_order + "H" * length 
    elif primary_type is U32:
        return byte_order + "I" * length 
    elif primary_type is U64:
        return byte_order + "Q" * length 
    elif primary_type is I8:
        return byte_order + "b" * length
    elif primary_type is I16:    
        return byte_order + "h" * length 
    elif primary_type is I32:
        return byte_order + "i" * length 
    elif primary_type is I64:
        return byte_order + "q" * length 
    elif primary_type is F16:
        return byte_order + "e" * length 
    elif primary_type is F32:
        return byte_order + "f" * length 
    elif primary_type is F64:
        return byte_order + "d" * length 
    elif primary_type is CHAR:
        return byte_order + "c" * length  
    elif primary_type is CHAR_ARRAY:
        return byte_order + f"{length}s" 
    else:
        raise ValueError(f"Unknown pod_type: {primary_type}") 
    

class ConsumeBuffer:
    """Thin wrapper around a buffer that keeps track of the cursor position.
    """

    def __init__(self, buffer: Buffer) -> None:
        self._buffer = buffer
        self._offset = 0

    def unpack(self, fmt: str) -> tuple[Any, ...]:
        """Read from the buffer, and updates the cursor position based
        on the fmt size.
        """
        delta = struct.calcsize(fmt)
        content = struct.unpack_from(fmt, self._buffer, self._offset)
        self._offset += delta
        return content
    

def _read(
        fmt: type[PrimaryTypes | ByteOrderSizeAlignment], 
        buffer: ConsumeBuffer, 
        byte_order: str, 
        record: dict[str, Any] | None=None
        ) -> Any:
    """Read helper

    Parameters
    ----------
    fmt
        Primary type, 
    buffer
        
    byte_order
        
    record, optional
        _description_, by default None

    Returns
    -------
        _description_
    """
    if fmt in _PrimaryTypesList:
        subfmt = build_format(fmt, byte_order, length=1)
        return buffer.unpack(subfmt)[0]
    
    elif get_origin(fmt) is Annotated:
        subfmt, length = get_args(fmt)
        is_list = False
        
        if get_origin(subfmt) is list:
            is_list = True
            subfmt = get_args(subfmt)[0]

        if isinstance(length, str):
            # The lengths is defined by another, previous, field.
            if record is None:
                raise ValueError(f"Could not find field {length}, no record given.")
            if length not in record:
                raise ValueError(f"Could not find field {length} in record.")
            length = record[length]
        
        if length == 0:
            if is_list:
                return []
            return None
        
        if subfmt in _PrimaryTypesList:
            if subfmt is not CHAR_ARRAY:
                assert length == 1
            subfmt2 = build_format(subfmt, byte_order, length)
            content = buffer.unpack(subfmt2)[0]
            return content
        else:
            return tuple(
                _read(subfmt, buffer, byte_order, length) 
                for _ in range(length)
            )
        
    elif is_typed_dict(fmt):
        byte_order = get_byte_order(fmt)
        record = {}
        for k, v in get_type_hints(fmt, include_extras=True).items():
            if k.startswith("_"):
                continue
            record[k] =_read(v, buffer, byte_order, record) 
        return record
    
    else:
        raise ValueError(f"Unknown format {fmt}")


def read[T: ByteOrderSizeAlignment](spec: type[T], buffer: Buffer) -> T:
    """
    """
    return _read(spec, ConsumeBuffer(buffer), "n")


