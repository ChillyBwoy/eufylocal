from datetime import UTC, datetime

import pytest

from eufylocal.parser import compute_checksum, extract_frame_from_manufacturer_data
from eufylocal.runtime import MeasurementHandler
from eufylocal.schemas import FinalMeasurementReceived, StatusEvent

FINAL_PAYLOAD = "cfe50c0301eccf2413122560655a0100914a9146"
RECEIVED_AT = datetime(2026, 9, 8, 10, 30, tzinfo=UTC)


def _final_frame() -> bytes:
    frame = extract_frame_from_manufacturer_data(bytes.fromhex(FINAL_PAYLOAD))
    assert frame is not None
    return frame


def _unstable_frame(frame: bytes) -> bytes:
    unstable = bytearray(frame)
    unstable[9] = 0x01
    unstable[10] = compute_checksum(unstable[:-1])
    return bytes(unstable)


@pytest.mark.asyncio
async def test_valid_frame_publishes_status_event() -> None:
    status_events: list[tuple[StatusEvent, dict[str, object]]] = []
    final_events: list[FinalMeasurementReceived] = []

    async def on_final(event: FinalMeasurementReceived) -> None:
        final_events.append(event)

    handler = MeasurementHandler(
        lambda event, **payload: status_events.append((event, payload)),
        on_final,
    )

    await handler.handle_frame(
        frame=_unstable_frame(_final_frame()),
        source="advertisement",
        device_id="DEVICE-1",
        received_at=RECEIVED_AT,
    )

    assert status_events == [
        (
            StatusEvent.READING_RECEIVED,
            {"received_at": RECEIVED_AT, "weight_kg": 94.9, "is_final": False},
        )
    ]
    assert final_events == []


@pytest.mark.asyncio
async def test_final_frame_publishes_measurement() -> None:
    final_events: list[FinalMeasurementReceived] = []

    async def on_final(event: FinalMeasurementReceived) -> None:
        final_events.append(event)

    handler = MeasurementHandler(lambda _event, **_payload: None, on_final)

    await handler.handle_frame(
        frame=_final_frame(),
        source="advertisement",
        device_id="DEVICE-1",
        received_at=RECEIVED_AT,
    )

    assert final_events == [
        FinalMeasurementReceived(
            measured_at=RECEIVED_AT,
            weight_kg=94.9,
            impedance_ohm=490.0,
            device_id="DEVICE-1",
            source="advertisement",
            raw_payload_hex=_final_frame().hex(),
        )
    ]


@pytest.mark.asyncio
async def test_invalid_frame_publishes_nothing() -> None:
    events: list[object] = []

    async def on_final(event: FinalMeasurementReceived) -> None:
        events.append(event)

    handler = MeasurementHandler(
        lambda event, **payload: events.append((event, payload)),
        on_final,
    )

    await handler.handle_frame(
        frame=b"\x00\x01\x02",
        source="advertisement",
        device_id="DEVICE-1",
        received_at=RECEIVED_AT,
    )

    assert events == []


@pytest.mark.asyncio
async def test_final_callback_error_is_propagated() -> None:
    async def on_final(_event: FinalMeasurementReceived) -> None:
        raise RuntimeError("insert failed")

    handler = MeasurementHandler(lambda _event, **_payload: None, on_final)

    with pytest.raises(RuntimeError, match="insert failed"):
        await handler.handle_frame(
            frame=_final_frame(),
            source="advertisement",
            device_id="DEVICE-1",
            received_at=RECEIVED_AT,
        )
