import pytest

from eufylocal.parser import (
    compute_checksum,
    extract_frame_from_manufacturer_data,
    parse_frame,
)
from eufylocal.schemas.measurement import MeasurementUnit

REAL_MANUFACTURER_DATA = [
    ("cfe50c0301eccf2413122560655a0100914a9146", 94.9, 490.0, "lb"),
    ("cfe50c0301eccf0a143a257975ed01002e4a9146", 95.3, 513.0, "lb"),
    ("cfe50c0301eccfa2128c232624540100874a9146", 91.0, 477.0, "lb"),
    ("cfe50c0301eccfa212b824ebe77401009a4a9146", 94.0, 477.0, "lb"),
    ("cfe50c0301eccfac12b824a0a6460100ac4a9146", 94.0, 478.0, "lb"),
]


def _frame(status: int, weight_raw: int = 9490) -> bytes:
    frame = bytearray(11)
    frame[0] = 0xCF
    frame[1] = 0x24
    frame[2] = 0x13
    frame[3] = weight_raw & 0xFF
    frame[4] = (weight_raw >> 8) & 0xFF
    frame[5] = 0x60
    frame[6] = 0x65
    frame[7] = 0x5A
    frame[8] = 0x01
    frame[9] = status
    frame[10] = compute_checksum(frame[:-1])
    return bytes(frame)


@pytest.mark.parametrize(
    ("payload", "expected_weight", "expected_impedance", "expected_unit"),
    REAL_MANUFACTURER_DATA,
)
def test_parse_real_manufacturer_data(
    payload: str, expected_weight: float, expected_impedance: float, expected_unit: str
) -> None:
    frame = extract_frame_from_manufacturer_data(bytes.fromhex(payload))
    assert frame is not None

    parsed = parse_frame(frame)
    assert parsed is not None
    assert parsed.weight == pytest.approx(expected_weight)
    assert parsed.impedance_ohm == pytest.approx(expected_impedance)
    assert parsed.is_final is True
    assert parsed.weight_limit_exceeded is False
    assert parsed.unit == expected_unit


def test_parse_final_frame() -> None:
    parsed = parse_frame(_frame(status=0x00))
    assert parsed is not None
    assert parsed.is_final is True
    assert parsed.weight_limit_exceeded is False


def test_parse_unstable_frame_is_not_final() -> None:
    parsed = parse_frame(_frame(status=0x01))
    assert parsed is not None
    assert parsed.is_final is False


def test_parse_weight_limit_exceeded() -> None:
    parsed = parse_frame(_frame(status=0x02))
    assert parsed is not None
    assert parsed.weight_limit_exceeded is True
    assert parsed.is_final is False


def test_parse_kg_unit() -> None:
    frame = bytearray(_frame(status=0x00))
    frame[8] = 0x00
    frame[10] = compute_checksum(frame[:-1])
    parsed = parse_frame(frame)
    assert parsed is not None
    assert parsed.unit == MeasurementUnit.KG


def test_parse_rejects_bad_checksum() -> None:
    frame = bytearray(_frame(status=0x00))
    frame[10] ^= 0xFF
    assert parse_frame(frame) is None


def test_parse_rejects_wrong_prefix() -> None:
    frame = bytearray(_frame(status=0x00))
    frame[0] = 0xCE
    assert parse_frame(frame) is None


def test_parse_rejects_wrong_length() -> None:
    frame = _frame(status=0x00)
    assert parse_frame(frame[:-1]) is None
    assert parse_frame(frame + b"\x00") is None


def test_parse_rejects_implausible_weight() -> None:
    frame = _frame(status=0x00, weight_raw=0xFFFF)
    assert parse_frame(frame) is None


def test_extract_frame_from_short_data() -> None:
    assert extract_frame_from_manufacturer_data(b"\x00\x01\x02") is None


def test_extract_frame_falls_back_to_checksum_scan() -> None:
    data = bytes.fromhex("aabb") + _frame(status=0x00) + b"\x91\x46"
    frame = extract_frame_from_manufacturer_data(data)
    assert frame == _frame(status=0x00)
