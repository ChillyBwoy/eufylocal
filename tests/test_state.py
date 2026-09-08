from __future__ import annotations

from datetime import UTC, datetime

import eufylocal.state as state_module
from eufylocal.db import MeasurementModel
from eufylocal.state import AppState


def test_live_weight_is_active_only_before_final_measurement() -> None:
    state = AppState()
    state.set_live_weight(75.1)
    assert state.snapshot()["bluetooth"]["live_weight_active"] is True

    state.set_last_measurement(
        MeasurementModel(
            measured_at=datetime.now(UTC),
            weight_kg=75.2,
            impedance_ohm=None,
            device_id="DEVICE-1",
            source="advertisement",
            raw_payload_hex="cf",
        )
    )
    snapshot = state.snapshot()
    assert snapshot["bluetooth"]["live_weight_active"] is False
    assert snapshot["last_measurement"].weight_kg == 75.2


def test_live_weight_expires(monkeypatch) -> None:
    current_time = 100.0
    monkeypatch.setattr(state_module.time, "monotonic", lambda: current_time)
    state = AppState()
    state.set_live_weight(75.1)

    current_time += 11.0
    snapshot = state.snapshot()

    assert snapshot["bluetooth"]["live_weight_active"] is False
    assert snapshot["bluetooth"]["live_weight_kg"] is None


def test_last_measurement_updates_last_received_at() -> None:
    measured_at = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
    state = AppState()
    state.set_last_measurement(
        MeasurementModel(
            measured_at=measured_at,
            weight_kg=80.0,
            impedance_ohm=None,
            device_id="DEVICE-1",
            source="advertisement",
            raw_payload_hex="cf",
        )
    )

    assert state.snapshot()["bluetooth"]["last_received_at"] == measured_at
