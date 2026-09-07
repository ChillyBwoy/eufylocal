from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy.exc import StatementError

from eufylocal.db import Database, Measurement, MeasurementRepository
from eufylocal.db.migration import upgrade_database


def _measurement(
    weight_kg: float = 80.5,
    impedance_ohm: float | None = 420.0,
    source: str = "advertisement",
) -> Measurement:
    return Measurement(
        measured_at=datetime.now(UTC),
        weight_kg=weight_kg,
        impedance_ohm=impedance_ohm,
        device_id="DEVICE-UUID-123",
        source=source,
        raw_payload_hex="cf00102a00000000000000",
    )


@asynccontextmanager
async def _repository(path: Path) -> AsyncIterator[MeasurementRepository]:
    upgrade_database(path)
    database = Database(path)
    try:
        async with database.session() as session:
            yield MeasurementRepository(session)
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_insert_and_latest(tmp_path) -> None:
    async with _repository(tmp_path / "test.db") as repository:
        await repository.insert(_measurement())

        latest = await repository.latest()
        assert latest is not None
        assert latest.weight_kg == 80.5
        assert latest.impedance_ohm == 420.0
        assert latest.raw_payload_hex == "cf00102a00000000000000"


@pytest.mark.asyncio
async def test_null_impedance_is_accepted(tmp_path) -> None:
    async with _repository(tmp_path / "test.db") as repository:
        await repository.insert(_measurement(impedance_ohm=None))
        latest = await repository.latest()
        assert latest is not None
        assert latest.impedance_ohm is None


@pytest.mark.asyncio
async def test_list_returns_newest_first(tmp_path) -> None:
    async with _repository(tmp_path / "test.db") as repository:
        await repository.insert(_measurement(weight_kg=1.0))
        await repository.insert(_measurement(weight_kg=2.0))
        await repository.insert(_measurement(weight_kg=3.0))

        items = await repository.list(limit=10)
        assert [m.weight_kg for m in items] == [3.0, 2.0, 1.0]
        assert (await repository.list(limit=2))[0].weight_kg == 3.0


@pytest.mark.asyncio
async def test_latest_empty(tmp_path) -> None:
    async with _repository(tmp_path / "test.db") as repository:
        assert await repository.latest() is None
        assert await repository.list() == []


@pytest.mark.asyncio
async def test_latest_uses_id_to_break_timestamp_ties(tmp_path) -> None:
    async with _repository(tmp_path / "test.db") as repository:
        measured_at = datetime.now(UTC)
        first = _measurement(weight_kg=80.0)
        second = _measurement(weight_kg=81.0)
        first.measured_at = measured_at
        second.measured_at = measured_at

        await repository.insert(first)
        await repository.insert(second)

        latest = await repository.latest()
        assert latest is not None
        assert latest.id == second.id


@pytest.mark.asyncio
async def test_naive_timestamp_rolls_back(tmp_path) -> None:
    async with _repository(tmp_path / "test.db") as repository:
        measurement = _measurement()
        measurement.measured_at = datetime.now()

        with pytest.raises(StatementError):
            await repository.insert(measurement)

        assert await repository.list() == []


@pytest.mark.asyncio
async def test_database_supports_concurrent_sessions(tmp_path) -> None:
    database_path = tmp_path / "test.db"
    upgrade_database(database_path)
    database = Database(database_path)

    async def insert(weight: float) -> None:
        async with database.session() as session:
            await MeasurementRepository(session).insert(_measurement(weight))

    try:
        await asyncio.gather(*(insert(weight) for weight in range(1, 9)))
        async with database.session() as session:
            assert len(await MeasurementRepository(session).list()) == 8
    finally:
        await database.close()
