
import dataclasses
import datetime
import pathlib
import struct
from itertools import chain
from typing import Literal

from .binary import F64, I32, I64, build_format
from .binary import read as llread
from .lowlevel import ContainerFile, byte_order_sigil

type MeasContext = Literal["Unknown", "Decay", "TRES", "AnisoDecay", "DecayTempSeries", "DecayTimeSeries",
                     "FluorSpec", "ExSpec", "FluorAnisoSpec", "ExAnisoSpec", "FluorSpecTimeSeries",
                     "ExSpecTimeSeries", "FluorSpecTempSeries", "ExSpecTempSeries"]

type CurveType = Literal["IRF", "Decay", "Spectrum", "Arbitrary"]
type AnisotropyType = Literal["VH", "VV", "VM", "HH", "HV", "HM", "AA"]


def safe_decode_str(s: bytes | None) -> str:
    if s is None:
        return ""
    try:
        return s.decode("ascii")
    except:
        return "?"

@dataclasses.dataclass(frozen=True)
class SystemParameter:
    identity: str
    display_name: str
    unit: str
    prefix: str
    precision: int
    data: int | float | str


@dataclasses.dataclass(frozen=True)
class SeriesParameter:
    identity: str
    display_name: str
    unit: str
    prefix: str
    precision: int
    start: float
    step: float
    end: float

@dataclasses.dataclass(frozen=True)
class MeasurementParameter:
    identity: str
    display_name: str
    unit: str
    prefix: str
    precision: int
    data: int | float | str


@dataclasses.dataclass(frozen=True)
class DataCurve:
    curve_type_value: int
    anisotropy_value: int 
    measurement_parameters: tuple[MeasurementParameter, ...]
    resolution: float
    first_x: float
    x: tuple[float, ...]
    y: tuple[int, ...]

    @property
    def curve_type(self) -> CurveType:
        match self.curve_type_value:
            case 0: 
                return "IRF"
            case 1: 
                return "Decay"
            case 2: 
                return "Spectrum"
            case 3: 
                return "Arbitrary"
            case _ as x:
                raise ValueError(f"Unknown curve type {x}")  

    @property
    def anistropy(self) -> AnisotropyType:
        match self.anisotropy_value:
            case 0: 
                return "VH"
            case 1: 
                return "VV"
            case 2: 
                return "VM"
            case 3: 
                return "HH"
            case 4:
                return "HV"
            case 5:
                return "HM"
            case 6:
                return "AA"
            case _ as x:
                raise ValueError(f"Unknown curve type {x}")  


@dataclasses.dataclass(frozen=True)
class ETCFile:
    identity: str
    version: int
    guid: str
    creation_date: datetime.datetime
    measurement_context_value: int
    system_parameters: tuple[SystemParameter, ...]
    series_parameters: tuple[SeriesParameter, ...]
    data_curves: tuple[DataCurve, ...]

    @property
    def measurement_context(self) -> MeasContext:
        match self.measurement_context_value:
            case 0: 
                return "Unknown"
            case 1: 
                return  "Decay"
            case 2: 
                return  "TRES"
            case 3: 
                return  "AnisoDecay"
            case 4: 
                return  "DecayTempSeries"
            case 5: 
                return  "DecayTimeSeries"
            case 6: 
                return  "FluorSpec"
            case 7: 
                return  "ExSpec"
            case 8: 
                return  "FluorAnisoSpec"
            case 9: 
                return  "ExAnisoSpec"
            case 10: 
                return  "FluorSpecTimeSeries"
            case 11: 
                return  "ExSpecTimeSeries"
            case 12: 
                return  "FluorSpecTempSeries"
            case 13: 
                return  "FluorSpecTempSeries"
            case _ as x:
                raise ValueError(f"Unknown measurement context {x}")


def bytes_to_guid(byte_string: bytes) -> str:
    """Convert a byte string to a Microsoft GUID"""
    
    # The Microsoft GUID format has five fields separated by dashes.  
    # since the endianness is mixed, we need to reverse the first three fields. 
    # https://en.wikipedia.org/wiki/Universally_unique_identifier#Encoding
    
    # big endian components, we swap the endianness 
    A = (bytes(reversed(component))
         for component
         in struct.unpack_from('4s2s2s', byte_string, 0))

    # little endian components, good as is. 
    B = struct.unpack_from('2s6s', byte_string, 8)

    return '-'.join(c.hex() for c in chain(A,B))


def _get_data(par_type: int, size: int, data: bytes) -> int | float | str:
    match par_type:
        case 0: # pdfInteger
            if size == 4:
                out = struct.unpack(build_format(I32, byte_order_sigil), data)[0]
            elif size == 8:
                out = struct.unpack(build_format(I64, byte_order_sigil), data)[0]
            else: 
                raise ValueError(f"Invalid size {size} for {par_type}")
            return int(out)
        case 1: # pdfFloat
            assert size == 8
            return float(struct.unpack(build_format(F64, byte_order_sigil), data)[0])
        case 2: # pdfString
            return safe_decode_str(data)
        case _:
            raise ValueError(f"Unknown ParType: {par_type}")


def read(path: pathlib.Path | str):
    if isinstance(path, str):
        path = pathlib.Path(path)
    
    content = llread(ContainerFile, path.read_bytes())
    assert content["Ident"] == b'EasyTau Container\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' 

    system_parameters: list[SystemParameter] = []
    for value in content["SysParam"]:
        system_parameters.append(
            SystemParameter(
                identity=safe_decode_str(value["SysParIdent"]),
                display_name=safe_decode_str(value["SysParDispNm"]),
                unit=safe_decode_str(value["SysParUnit"]),
                prefix=safe_decode_str(value["SysParPrefix"]),
                precision=value["Precision"],
                data=_get_data(value["ParType"], value["Size"], value["Data"]),
            )
        )

        system_parameters: list[SystemParameter] = []

    series_parameters: list[SeriesParameter] = []
    for value in content["SeriesParam"]:
        series_parameters.append(
            SeriesParameter(
                identity=safe_decode_str(value["SeriesParIdent"]),
                display_name=safe_decode_str(value["SeriesParDispNm"]),
                unit=safe_decode_str(value["SeriesParUnit"]),
                prefix=safe_decode_str(value["SeriesParPrefix"]),
                precision=value["Precision"],
                start=value["Start"],
                step=value["Step"],
                end=value["End"]
            )
        )

    data_curves: list[DataCurve] = []
    measurement_parameters: list[MeasurementParameter] = []
    for value in content["Curve"]:
        measurement_parameters.clear()
        for subvalue in value["MeasParam"]:
            measurement_parameters.append(
                MeasurementParameter(
                    identity=safe_decode_str(subvalue["MeasParIdent"]),
                    display_name=safe_decode_str(subvalue["SeriesParDispNm"]),
                    unit=safe_decode_str(subvalue["SeriesParUnit"]),
                    prefix=safe_decode_str(subvalue["SeriesParPrefix"]),
                    precision=subvalue["Precision"],
                    data=_get_data(subvalue["ParType"], subvalue["Size"], subvalue["Data"])
                )
            )
        el = DataCurve(
            curve_type_value=value["CurveType"],
            anisotropy_value=value["Anisotropy"],
            measurement_parameters=tuple(measurement_parameters),
            resolution=value["Resolution"],
            first_x=value["FirstX"],
            x=tuple(item["X"] for item in value["XY"]),
            y=tuple(item["Y"] for item in value["XY"]),
        )
        data_curves.append(el)


    return ETCFile(
        identity=safe_decode_str(content["Ident"].strip(b"\x00")),
        version=content["Version"],
        guid=bytes_to_guid(content["GUID"]),
        creation_date=datetime.datetime(1899, 12, 30) + datetime.timedelta(content["CreationDate"]),
        measurement_context_value=content["MeasContext"],
        system_parameters=tuple(system_parameters),
        series_parameters=tuple(series_parameters),
        data_curves=tuple(data_curves),
    )



