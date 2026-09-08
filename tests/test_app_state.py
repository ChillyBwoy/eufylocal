from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eufylocal.runtime import LIVE_WEIGHT_TTL_SECONDS, AppState
from eufylocal.schemas import BLEStatus, BluetoothStatus, StatusEvent


def test_current_returns_typed_status() -> None:
    status = AppState().current()

    assert isinstance(status, BluetoothStatus)
    assert status.status is BLEStatus.IDLE
    assert status.live_weight_active is False


def test_reading_event_updates_weight_and_timestamp() -> None:
    received_at = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
    state = AppState()

    state.apply(
        StatusEvent.READING_RECEIVED,
        received_at=received_at,
        weight_kg=75.1,
    )

    status = state.current()
    assert status.last_received_at == received_at
    assert status.live_weight_kg == 75.1
    assert status.live_weight_active is True


def test_live_weight_expires_without_mutating_stored_status() -> None:
    current_time = 100.0
    state = AppState(monotonic=lambda: current_time)
    state.apply(
        StatusEvent.READING_RECEIVED,
        received_at=datetime.now(UTC),
        weight_kg=75.1,
    )

    current_time += LIVE_WEIGHT_TTL_SECONDS
    expired = state.current()

    assert expired.live_weight_active is False
    assert expired.live_weight_kg is None

    current_time -= 1
    assert state.current().live_weight_active is True


def test_connection_events_are_atomic() -> None:
    state = AppState()
    state.apply(StatusEvent.PROCESSING_FAILED, message="failed")
    state.apply(StatusEvent.CONNECTION_ESTABLISHED)

    connected = state.current()
    assert connected.status is BLEStatus.CONNECTED
    assert connected.last_error is None

    state.apply(StatusEvent.CONNECTION_LOST)
    assert state.current().status is BLEStatus.SCANNING


def test_status_schema_is_immutable() -> None:
    status = AppState().current()

    with pytest.raises(ValidationError):
        status.status = BLEStatus.ERROR
