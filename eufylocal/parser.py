from __future__ import annotations

from eufylocal.schemas.frame import ParsedFrame
from eufylocal.schemas.measurement import MeasurementUnit

FRAME_LENGTH = 11
FRAME_PREFIX = 0xCF

STATUS_FINAL = 0x00
STATUS_WEIGHT_LIMIT_EXCEEDED = 0x02

PLAUSIBLE_WEIGHT_KG = (1.0, 200.0)
PLAUSIBLE_IMPEDANCE_OHM = (100.0, 2000.0)


def compute_checksum(data: bytes | bytearray) -> int:
    checksum = 0
    for byte in data:
        checksum ^= byte
    return checksum


def validate_checksum(data: bytes | bytearray) -> bool:
    return len(data) > 1 and compute_checksum(data[:-1]) == data[-1]


def parse_frame(frame: bytes | bytearray) -> ParsedFrame | None:
    if len(frame) != FRAME_LENGTH or frame[0] != FRAME_PREFIX:
        return None

    if not validate_checksum(frame):
        return None

    weight_raw = (frame[4] << 8) | frame[3]
    weight_kg = weight_raw / 100
    if not (PLAUSIBLE_WEIGHT_KG[0] <= weight_kg <= PLAUSIBLE_WEIGHT_KG[1]):
        return None

    status = frame[9]
    is_final = status == STATUS_FINAL
    weight_limit_exceeded = status == STATUS_WEIGHT_LIMIT_EXCEEDED

    impedance_ohm: float | None = None
    if is_final:
        impedance_raw = (frame[2] << 8) | frame[1]
        impedance_ohm = impedance_raw / 10
        if not (PLAUSIBLE_IMPEDANCE_OHM[0] <= impedance_ohm <= PLAUSIBLE_IMPEDANCE_OHM[1]):
            impedance_ohm = None

    unit = MeasurementUnit.LB if frame[8] & 0x01 else MeasurementUnit.KG

    return ParsedFrame(
        weight=round(weight_kg, 2),
        impedance_ohm=round(impedance_ohm) if impedance_ohm is not None else None,
        weight_limit_exceeded=weight_limit_exceeded,
        unit=unit,
        is_final=is_final,
        raw=frame.hex(),
    )


def extract_frame_from_manufacturer_data(data: bytes | bytearray) -> bytes | None:
    if len(data) == 20 and data[18:20] == b"\x91\x46":
        return bytes(data[6:17])

    for offset in range(len(data) - FRAME_LENGTH + 1):
        if data[offset] != FRAME_PREFIX:
            continue
        candidate = bytes(data[offset : offset + FRAME_LENGTH])
        if parse_frame(candidate) is not None:
            return candidate

    return None
