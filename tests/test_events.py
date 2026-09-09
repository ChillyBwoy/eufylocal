import asyncio
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

import eufylocal.runtime.app_state as app_state_module
import eufylocal.runtime.runtime as runtime_module
from eufylocal.db import MeasurementRepository
from eufylocal.routes.events import event_stream, server_events
from eufylocal.runtime import EventBus, Runtime
from eufylocal.schemas import StatusEvent


@pytest.mark.asyncio
async def test_event_bus_coalesces_refreshes() -> None:
    events = EventBus()
    queue = events.subscribe()

    events.publish()
    events.publish()

    assert await queue.get() is None
    assert queue.empty()

    events.unsubscribe(queue)
    events.publish()
    assert queue.empty()


@pytest.mark.asyncio
async def test_event_stream_sends_ready_refresh_and_keepalive() -> None:
    events = EventBus()
    stream = event_stream(events, keepalive_seconds=0.01)

    assert await anext(stream) == "event: ready\ndata: {}\n\n"

    events.publish()
    assert await anext(stream) == "event: refresh\ndata: {}\n\n"
    assert await anext(stream) == ": keepalive\n\n"

    await stream.aclose()


@pytest.mark.asyncio
async def test_event_endpoint_configures_streaming_response() -> None:
    response = await server_events(EventBus())

    assert response.media_type == "text/event-stream"
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"

    await response.body_iterator.aclose()


@pytest.mark.asyncio
async def test_runtime_publishes_only_changed_status(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        runtime = Runtime(MeasurementRepository(session))
        queue = runtime.events.subscribe()

        runtime.apply_status(StatusEvent.SCAN_STARTED)
        assert await queue.get() is None

        runtime.apply_status(StatusEvent.SCAN_STARTED)
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(queue.get(), timeout=0.01)


@pytest.mark.asyncio
async def test_runtime_deduplicates_repeated_readings(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        runtime = Runtime(MeasurementRepository(session))
        queue = runtime.events.subscribe()

        runtime.apply_status(
            StatusEvent.READING_RECEIVED,
            received_at=datetime(2026, 9, 9, 10, 0, tzinfo=UTC),
            weight_kg=75.0,
            is_final=True,
        )
        assert await queue.get() is None

        runtime.apply_status(
            StatusEvent.READING_RECEIVED,
            received_at=datetime(2026, 9, 9, 10, 0, 1, tzinfo=UTC),
            weight_kg=75.0,
            is_final=True,
        )
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(queue.get(), timeout=0.01)


@pytest.mark.asyncio
async def test_runtime_publishes_when_live_weight_expires(
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch,
) -> None:
    monkeypatch.setattr(app_state_module, "LIVE_WEIGHT_TTL_SECONDS", 0.01)
    monkeypatch.setattr(runtime_module, "LIVE_WEIGHT_TTL_SECONDS", 0.01)

    async with session_factory() as session:
        runtime = Runtime(MeasurementRepository(session))
        queue = runtime.events.subscribe()
        runtime.apply_status(
            StatusEvent.READING_RECEIVED,
            received_at=datetime.now(UTC),
            weight_kg=75.0,
        )

        assert await queue.get() is None
        assert await asyncio.wait_for(queue.get(), timeout=0.1) is None
        assert runtime.state.current().live_weight_active is False
