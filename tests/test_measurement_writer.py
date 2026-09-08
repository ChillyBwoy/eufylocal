import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from eufylocal.db import MeasurementRepository
from eufylocal.runtime import MeasurementWriter
from eufylocal.schemas import FinalMeasurementReceived

RECEIVED_AT = datetime(2026, 9, 8, 10, 30, tzinfo=UTC)


def _measurement(payload: str = "frame-a") -> FinalMeasurementReceived:
    return FinalMeasurementReceived(
        measured_at=RECEIVED_AT,
        weight_kg=80.0,
        impedance_ohm=500.0,
        device_id="DEVICE-1",
        source="advertisement",
        raw_payload_hex=payload,
    )


@pytest.mark.asyncio
async def test_writer_persists_measurement(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        writer = MeasurementWriter(MeasurementRepository(session))
        await writer(_measurement())

    async with session_factory() as session:
        latest = await MeasurementRepository(session).latest()
    assert latest is not None
    assert latest.weight_kg == 80.0
    assert latest.measured_at == RECEIVED_AT


@pytest.mark.asyncio
async def test_writer_deduplicates_concurrent_and_restarted_writes(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        writer = MeasurementWriter(MeasurementRepository(session))
        await asyncio.gather(writer(_measurement()), writer(_measurement()))

    async with session_factory() as session:
        restarted = MeasurementWriter(MeasurementRepository(session))
        await restarted(_measurement())

    async with session_factory() as session:
        assert len(await MeasurementRepository(session).list()) == 1


@pytest.mark.asyncio
async def test_different_final_allows_previous_payload_again(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        writer = MeasurementWriter(MeasurementRepository(session))
        await writer(_measurement("frame-a"))
        await writer(
            FinalMeasurementReceived(
                measured_at=RECEIVED_AT + timedelta(seconds=1),
                weight_kg=81.0,
                impedance_ohm=510.0,
                device_id="DEVICE-1",
                source="gatt",
                raw_payload_hex="frame-b",
            )
        )
        await writer(
            FinalMeasurementReceived(
                measured_at=RECEIVED_AT + timedelta(seconds=2),
                weight_kg=80.0,
                impedance_ohm=500.0,
                device_id="DEVICE-1",
                source="advertisement",
                raw_payload_hex="frame-a",
            )
        )

    async with session_factory() as session:
        assert len(await MeasurementRepository(session).list()) == 3


@pytest.mark.asyncio
async def test_failed_insert_can_be_retried(
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch,
) -> None:
    async with session_factory() as session:
        repository = MeasurementRepository(session)
        writer = MeasurementWriter(repository)
        insert = repository.insert

        async def fail_once(_measurement) -> None:
            await repository.session.rollback()
            raise RuntimeError("insert failed")

        monkeypatch.setattr(repository, "insert", fail_once)
        with pytest.raises(RuntimeError, match="insert failed"):
            await writer(_measurement())

        monkeypatch.setattr(repository, "insert", insert)
        await writer(_measurement())

    async with session_factory() as session:
        assert len(await MeasurementRepository(session).list()) == 1


@pytest.mark.asyncio
async def test_failed_dedup_read_can_be_retried(
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch,
) -> None:
    async with session_factory() as session:
        repository = MeasurementRepository(session)
        writer = MeasurementWriter(repository)
        latest = repository.latest

        async def fail_once():
            raise RuntimeError("read failed")

        monkeypatch.setattr(repository, "latest", fail_once)
        with pytest.raises(RuntimeError, match="read failed"):
            await writer(_measurement())

        monkeypatch.setattr(repository, "latest", latest)
        await writer(_measurement())

    async with session_factory() as session:
        assert len(await MeasurementRepository(session).list()) == 1
