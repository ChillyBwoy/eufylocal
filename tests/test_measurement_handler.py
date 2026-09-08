from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import OperationalError

from eufylocal.db import Database, MeasurementModel, MeasurementRepository
from eufylocal.db.migration import upgrade_database
from eufylocal.measurement_handler import MeasurementHandler
from eufylocal.parser import compute_checksum, extract_frame_from_manufacturer_data
from eufylocal.state import AppState

FINAL_PAYLOAD = "cfe50c0301eccf2413122560655a0100914a9146"
DIFFERENT_FINAL_PAYLOAD = "cfe50c0301eccf0a143a257975ed01002e4a9146"
RECEIVED_AT = datetime(2026, 9, 8, 10, 30, tzinfo=UTC)


def _final_frame(payload: str = FINAL_PAYLOAD) -> bytes:
    frame = extract_frame_from_manufacturer_data(bytes.fromhex(payload))
    assert frame is not None
    return frame


def _unstable_frame(frame: bytes) -> bytes:
    unstable = bytearray(frame)
    unstable[9] = 0x01
    unstable[10] = compute_checksum(unstable[:-1])
    return bytes(unstable)


async def _handle(
    handler: MeasurementHandler,
    frame: bytes,
    source: str = "advertisement",
    device_id: str = "DEVICE-1",
    received_at: datetime = RECEIVED_AT,
) -> None:
    await handler.handle_frame(
        frame=frame,
        source=source,
        device_id=device_id,
        received_at=received_at,
    )


@pytest.mark.asyncio
async def test_final_frame_is_persisted_with_received_time(tmp_path) -> None:
    database_path = tmp_path / "handler.db"
    upgrade_database(database_path)
    database = Database(database_path)
    state = AppState()
    handler = MeasurementHandler(database, state)

    await _handle(handler, _unstable_frame(_final_frame()))

    snapshot = state.snapshot()
    assert snapshot["bluetooth"]["last_received_at"] == RECEIVED_AT
    assert snapshot["bluetooth"]["live_weight_active"] is True
    assert snapshot["last_measurement"] is None

    await _handle(handler, _final_frame())

    async with database.session() as session:
        latest = await MeasurementRepository(session).latest()
    await database.close()

    assert latest is not None
    assert latest.weight_kg == 94.9
    assert latest.measured_at == RECEIVED_AT
    snapshot = state.snapshot()
    assert snapshot["last_measurement"].weight_kg == 94.9
    assert snapshot["bluetooth"]["live_weight_active"] is False


@pytest.mark.asyncio
async def test_invalid_frame_is_ignored_without_state_changes(tmp_path) -> None:
    database_path = tmp_path / "invalid.db"
    upgrade_database(database_path)
    database = Database(database_path)
    state = AppState()
    handler = MeasurementHandler(database, state)

    await _handle(handler, b"\x00\x01\x02")

    async with database.session() as session:
        assert await MeasurementRepository(session).list() == []
    await database.close()

    snapshot = state.snapshot()
    assert snapshot["bluetooth"]["last_received_at"] is None
    assert snapshot["last_measurement"] is None


@pytest.mark.asyncio
async def test_duplicate_final_frame_requires_a_different_final_frame(tmp_path) -> None:
    database_path = tmp_path / "dedup.db"
    upgrade_database(database_path)
    database = Database(database_path)
    state = AppState()
    frame = _final_frame()
    different_frame = _final_frame(DIFFERENT_FINAL_PAYLOAD)
    handler = MeasurementHandler(database, state)

    await asyncio.gather(
        _handle(handler, frame),
        _handle(handler, frame, source="gatt"),
    )

    async with database.session() as session:
        repository = MeasurementRepository(session)
        assert len(await repository.list()) == 1
        latest = await repository.latest()
    assert latest is not None

    restarted = MeasurementHandler(database, AppState(), latest)
    await _handle(restarted, frame)
    async with database.session() as session:
        assert len(await MeasurementRepository(session).list()) == 1

    await _handle(restarted, _unstable_frame(frame))
    await _handle(restarted, frame)
    async with database.session() as session:
        assert len(await MeasurementRepository(session).list()) == 1

    await _handle(restarted, different_frame)
    await _handle(restarted, frame)
    async with database.session() as session:
        assert len(await MeasurementRepository(session).list()) == 3
    await database.close()


@pytest.mark.asyncio
async def test_insert_error_does_not_update_state_or_dedup_key(tmp_path) -> None:
    database = Database(tmp_path / "missing" / "error.db")
    state = AppState()
    handler = MeasurementHandler(database, state)

    with pytest.raises(OperationalError):
        await _handle(handler, _final_frame())

    assert state.snapshot()["last_measurement"] is None
    assert handler._last_persisted_key is None
    await database.close()


@pytest.mark.asyncio
async def test_restart_seeds_last_received_at_from_latest(tmp_path) -> None:
    database_path = tmp_path / "seed.db"
    upgrade_database(database_path)
    database = Database(database_path)
    seeded = MeasurementModel.from_received(
        received_at=RECEIVED_AT,
        weight_kg=94.9,
        impedance_ohm=490.0,
        device_id="DEVICE-1",
        source="advertisement",
        raw_payload_hex=_final_frame().hex(),
    )

    async with database.session() as session:
        await MeasurementRepository(session).insert(seeded)

    runtime = AppState()
    async with database.session() as session:
        latest = await MeasurementRepository(session).latest()
    assert latest is not None
    runtime.set_last_measurement(latest)

    handler = MeasurementHandler(database, runtime, latest)
    await _handle(handler, _final_frame())

    async with database.session() as session:
        assert len(await MeasurementRepository(session).list()) == 1
    await database.close()
    assert runtime.snapshot()["bluetooth"]["last_received_at"] == RECEIVED_AT
