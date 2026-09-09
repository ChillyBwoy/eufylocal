import asyncio
from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from eufylocal.db import MeasurementModel, MeasurementRepository


def _measurement(
    weight_kg: float = 80.5,
    impedance_ohm: float | None = 420.0,
    source: str = "advertisement",
) -> MeasurementModel:
    return MeasurementModel(
        measured_at=datetime.now(UTC),
        weight_kg=weight_kg,
        impedance_ohm=impedance_ohm,
        device_id="DEVICE-UUID-123",
        source=source,
        raw_payload_hex="cf00102a00000000000000",
    )


@pytest.mark.asyncio
async def test_insert_and_latest(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        repository = MeasurementRepository(session)
        await repository.insert(_measurement())
        latest = await repository.latest()

    assert latest is not None
    assert latest.weight_kg == 80.5
    assert latest.impedance_ohm == 420.0
    assert latest.raw_payload_hex == "cf00102a00000000000000"


@pytest.mark.asyncio
async def test_null_impedance_is_accepted(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        repository = MeasurementRepository(session)
        await repository.insert(_measurement(impedance_ohm=None))
        latest = await repository.latest()
    assert latest is not None
    assert latest.impedance_ohm is None


@pytest.mark.asyncio
async def test_list_returns_newest_first(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        repository = MeasurementRepository(session)
        await repository.insert(_measurement(weight_kg=1.0))
        await repository.insert(_measurement(weight_kg=2.0))
        await repository.insert(_measurement(weight_kg=3.0))
        items = await repository.list(limit=10)

    assert [measurement.weight_kg for measurement in items] == [3.0, 2.0, 1.0]


@pytest.mark.asyncio
async def test_latest_empty(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        repository = MeasurementRepository(session)
        assert await repository.latest() is None
        assert await repository.list() == []


@pytest.mark.asyncio
async def test_latest_uses_insertion_order(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        repository = MeasurementRepository(session)
        first = _measurement(weight_kg=80.0)
        second = _measurement(weight_kg=81.0)
        second.measured_at = first.measured_at.replace(year=first.measured_at.year - 1)
        await repository.insert(first)
        await repository.insert(second)
        latest = await repository.latest()

    assert latest is not None
    assert latest.id == second.id


@pytest.mark.asyncio
async def test_timestamp_round_trips_in_utc(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        repository = MeasurementRepository(session)
        measurement = _measurement()
        measurement.measured_at = datetime(
            2026,
            9,
            9,
            15,
            30,
            tzinfo=timezone(timedelta(hours=3)),
        )

        await repository.insert(measurement)
        latest = await repository.latest()

        assert latest is not None
        assert latest.measured_at == datetime(2026, 9, 9, 12, 30, tzinfo=UTC)


@pytest.mark.asyncio
async def test_database_supports_concurrent_sessions(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def insert(weight: float) -> None:
        async with session_factory() as session:
            await MeasurementRepository(session).insert(_measurement(weight))

    await asyncio.gather(*(insert(weight) for weight in range(1, 9)))

    async with session_factory() as session:
        assert len(await MeasurementRepository(session).list()) == 8
