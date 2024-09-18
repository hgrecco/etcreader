
from typing import Annotated

from . import binary

ByteOrderClass = binary.LittleEndian
byte_order_sigil = binary.get_byte_order(ByteOrderClass)


class SysParam(ByteOrderClass):
    SysParIdLgt: binary.I32
    SysParIdent: Annotated[binary.CHAR_ARRAY, "SysParIdLgt"]
    SysParDispNmLgt: binary.I32
    SysParDispNm: Annotated[binary.CHAR_ARRAY, "SysParDispNmLgt"]
    SysParUnitLgt: binary.I32
    SysParUnit: Annotated[binary.CHAR_ARRAY, "SysParUnitLgt"]
    SysParPrefixLgt: binary.I32
    SysParPrefix: Annotated[binary.CHAR_ARRAY, "SysParPrefixLgt"]    
    Precision: binary.I32
    ParType: binary.I32
    Size: binary.I32
    Data: Annotated[binary.CHAR_ARRAY, "Size"]


class SeriesParam(ByteOrderClass):
    SeriesParIdLgt: binary.I32
    SeriesParIdent: Annotated[binary.CHAR_ARRAY, "SeriesParIdLgt"]
    SeriesParDispNmLgt: binary.I32
    SeriesParDispNm: Annotated[binary.CHAR_ARRAY, "SeriesParDispNmLgt"]
    SeriesParUnitLgt: binary.I32
    SeriesParUnit: Annotated[binary.CHAR_ARRAY, "SeriesParUnitLgt"]
    SeriesParPrefixLgt: binary.I32
    SeriesParPrefix: Annotated[binary.CHAR_ARRAY, "SeriesParPrefixLgt"]    
    Precision: binary.I32
    Start: binary.F32
    Step: binary.F32
    End: binary.F32


class MeasParam(ByteOrderClass):
    MeasParIdLgt: binary.I32
    MeasParIdent: Annotated[binary.CHAR_ARRAY, "MeasParIdLgt"]
    SeriesParDispNmLgt: binary.I32
    SeriesParDispNm: Annotated[binary.CHAR_ARRAY, "SeriesParDispNmLgt"]
    SeriesParUnitLgt: binary.I32
    SeriesParUnit: Annotated[binary.CHAR_ARRAY, "SeriesParUnitLgt"]
    SeriesParPrefixLgt: binary.I32
    SeriesParPrefix: Annotated[binary.CHAR_ARRAY, "SeriesParPrefixLgt"]    
    Precision: binary.I32
    ParType: binary.I32
    Size: binary.I32
    Data: Annotated[binary.CHAR_ARRAY, "Size"]


class XY(ByteOrderClass):
    X: binary.F32
    Y: binary.I32


class DataCurve(ByteOrderClass):
    CurveType: binary.I32
    Anisotropy: binary.I32
    Resolution: binary.F32
    FirstX: binary.F32
    MeasParamCount: binary.I32
    MeasParam: Annotated[list[MeasParam], "MeasParamCount"]
    NumPoints: binary.I32
    XY: Annotated[list[XY], "NumPoints"]


class ContainerFile(ByteOrderClass):

    Ident: Annotated[binary.CHAR_ARRAY, 32]
    Version: binary.I32
    GUID: Annotated[binary.CHAR_ARRAY, 16]
    CreationDate: binary.F64
    MeasContext: binary.I32
    SysParamCount: binary.I32
    SysParam: Annotated[list[SysParam], "SysParamCount"]
    SeriesParamCount: binary.I32
    SeriesParam: Annotated[list[SeriesParam], "SeriesParamCount"]
    CurveCount: binary.I32
    Curve: Annotated[list[DataCurve], "CurveCount"]

