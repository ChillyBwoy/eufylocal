from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

import eufylocal.ble_collector as ble_module
import eufylocal.state as state_module
from eufylocal.ble_collector import BLECollector, scan_and_print
from eufylocal.config import Settings
from eufylocal.db import Database, Measurement, MeasurementRepository
from eufylocal.db.migration import upgrade_database
from eufylocal.parser import extract_frame_from_manufacturer_data
from eufylocal.state import AppState


def _device(address: str = "DEVICE-1", name: str = "eufy T9146") -> SimpleNamespace:
    return SimpleNamespace(address=address, name=name)


def _advertisement(name: str = "eufy T9146") -> SimpleNamespace:
    return SimpleNamespace(local_name=name, rssi=-50, manufacturer_data={1: b"payload"})


def _settings(**values: object) -> Settings:
    return Settings(_env_file=None, **values)


def _collector(settings: Settings) -> BLECollector:
    return BLECollector(settings, Database(Path(":memory:")), AppState())


def test_configured_identifier_rejects_other_named_scale() -> None:
    collector = _collector(_settings(device_identifier="SELECTED"))

    assert collector._matches(_device("OTHER"), _advertisement()) is False
    assert collector._matches(_device("selected"), _advertisement("other")) is True


def test_name_is_used_when_identifier_is_not_configured() -> None:
    collector = _collector(_settings())

    assert collector._matches(_device(name="eufy T9146"), _advertisement()) is True
    assert collector._matches(_device(name="other"), _advertisement("other")) is False


def test_live_weight_is_active_only_before_final_measurement() -> None:
    state = AppState()
    state.set_live_weight(75.1)
    assert state.snapshot()["bluetooth"]["live_weight_active"] is True

    state.set_last_measurement(
        Measurement(
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


@pytest.mark.asyncio
async def test_final_frame_is_persisted_async(tmp_path) -> None:
    database_path = tmp_path / "collector.db"
    upgrade_database(database_path)
    database = Database(database_path)
    state = AppState()
    collector = BLECollector(_settings(), database, state)
    frame = extract_frame_from_manufacturer_data(
        bytes.fromhex("cfe50c0301eccf2413122560655a0100914a9146")
    )
    assert frame is not None

    collector._schedule_frame(_device(), frame, "advertisement")
    await collector._drain_callback_tasks()

    async with database.session() as session:
        latest = await MeasurementRepository(session).latest()
    await database.close()
    assert latest is not None
    assert latest.weight_kg == 94.9
    assert state.snapshot()["last_measurement"].weight_kg == 94.9


def test_gatt_listener_returns_after_disconnect(monkeypatch) -> None:
    class FakeClient:
        def __init__(self, device, disconnected_callback) -> None:
            self.address = device.address
            self.is_connected = False
            self._disconnected_callback = disconnected_callback

        async def connect(self) -> None:
            self.is_connected = True

        async def start_notify(self, _uuid, _callback) -> None:
            self.is_connected = False
            self._disconnected_callback(self)

        async def disconnect(self) -> None:
            self.is_connected = False

    monkeypatch.setattr(ble_module, "BleakClient", FakeClient)
    state = AppState()
    collector = BLECollector(_settings(), Database(Path(":memory:")), state)

    asyncio.run(collector._connect_and_listen(_device()))

    assert state.snapshot()["bluetooth"]["status"] == "scanning"


def test_gatt_disconnects_when_notification_setup_fails(monkeypatch) -> None:
    clients = []

    class FakeClient:
        def __init__(self, device, disconnected_callback) -> None:
            self.address = device.address
            self.is_connected = False
            self.disconnected = False
            clients.append(self)

        async def connect(self) -> None:
            self.is_connected = True

        async def start_notify(self, _uuid, _callback) -> None:
            raise RuntimeError("subscription failed")

        async def disconnect(self) -> None:
            self.is_connected = False
            self.disconnected = True

    monkeypatch.setattr(ble_module, "BleakClient", FakeClient)
    collector = _collector(_settings())

    try:
        asyncio.run(collector._connect_and_listen(_device()))
    except RuntimeError as exc:
        assert str(exc) == "subscription failed"
    else:
        raise AssertionError("notification setup error was not propagated")

    assert clients[0].disconnected is True


def test_dump_logs_repeated_payloads(monkeypatch, caplog) -> None:
    class FakeScanner:
        def __init__(self, detection_callback) -> None:
            self._callback = detection_callback

        async def start(self) -> None:
            device = _device()
            advertisement = _advertisement()
            self._callback(device, advertisement)
            advertisement.manufacturer_data = {1: b"changed"}
            self._callback(device, advertisement)

        async def stop(self) -> None:
            pass

    monkeypatch.setattr(ble_module, "BleakScanner", FakeScanner)
    caplog.set_level(logging.INFO, logger=ble_module.__name__)

    asyncio.run(scan_and_print(_settings(), 0, repeat_payloads=True))

    messages = [record.message for record in caplog.records if "device found" in record.message]
    assert len(messages) == 2
    assert "7061796c6f6164" in messages[0]
    assert "6368616e676564" in messages[1]


def test_scan_logs_each_device_once(monkeypatch, caplog) -> None:
    class FakeScanner:
        def __init__(self, detection_callback) -> None:
            self._callback = detection_callback

        async def start(self) -> None:
            self._callback(_device(), _advertisement())
            self._callback(_device(), _advertisement())

        async def stop(self) -> None:
            pass

    monkeypatch.setattr(ble_module, "BleakScanner", FakeScanner)
    caplog.set_level(logging.INFO, logger=ble_module.__name__)

    asyncio.run(scan_and_print(_settings(), 0))

    messages = [record.message for record in caplog.records if "device found" in record.message]
    assert len(messages) == 1
