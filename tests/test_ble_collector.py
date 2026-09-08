from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

import eufylocal.ble_collector as ble_module
from eufylocal.ble_collector import BLECollector, scan_and_print
from eufylocal.config import Settings
from eufylocal.parser import extract_frame_from_manufacturer_data
from eufylocal.state import AppState


def _device(address: str = "DEVICE-1", name: str = "eufy T9146") -> SimpleNamespace:
    return SimpleNamespace(address=address, name=name)


def _advertisement(name: str = "eufy T9146") -> SimpleNamespace:
    return SimpleNamespace(local_name=name, rssi=-50, manufacturer_data={1: b"payload"})


def _settings(**values: object) -> Settings:
    return Settings(_env_file=None, **values)


async def _ignore_frame(**_kwargs) -> None:
    pass


def _collector(settings: Settings, state: AppState | None = None) -> BLECollector:
    return BLECollector(settings, state or AppState(), _ignore_frame)


def test_configured_identifier_rejects_other_named_scale() -> None:
    collector = _collector(_settings(device_identifier="SELECTED"))

    assert collector._matches(_device("OTHER"), _advertisement()) is False
    assert collector._matches(_device("selected"), _advertisement("other")) is True


def test_name_is_used_when_identifier_is_not_configured() -> None:
    collector = _collector(_settings())

    assert collector._matches(_device(name="eufy T9146"), _advertisement()) is True
    assert collector._matches(_device(name="other"), _advertisement("other")) is False


def test_matching_advertisement_logs_all_data(caplog) -> None:
    collector = _collector(_settings())
    device = _device()
    advertisement = _advertisement()

    with caplog.at_level(logging.INFO):
        collector._on_advertisement(device, advertisement)

    assert "scale advertisement" in caplog.text
    assert "DEVICE-1" in caplog.text
    assert "manufacturer_data={1: b'payload'}" in caplog.text


@pytest.mark.asyncio
async def test_gatt_notification_logs_sender_and_raw_data(caplog) -> None:
    collector = _collector(_settings())
    sender = SimpleNamespace(uuid="fff4", handle=4)

    with caplog.at_level(logging.INFO):
        collector._on_gatt_notification(sender, bytearray.fromhex("0102ff"))
        await collector._drain_callback_tasks()

    assert "scale GATT notification" in caplog.text
    assert "uuid='fff4'" in caplog.text
    assert "data=0102ff" in caplog.text


@pytest.mark.asyncio
async def test_scheduled_frame_passes_normalized_arguments(monkeypatch) -> None:
    received_at = datetime(2026, 9, 8, 10, 30, tzinfo=UTC)

    class FakeDateTime:
        @classmethod
        def now(cls, timezone):
            assert timezone is UTC
            return received_at

    monkeypatch.setattr(ble_module, "datetime", FakeDateTime)
    captured: list[dict] = []

    async def capture(**kwargs) -> None:
        captured.append(kwargs)

    collector = BLECollector(_settings(), AppState(), capture)
    mutable = bytearray.fromhex("cfe50c0301eccf2413122560655a010091")

    collector._schedule_frame(_device(), mutable, "advertisement")
    mutable[0] = 0x00
    await collector._drain_callback_tasks()

    assert captured == [
        {
            "frame": bytes.fromhex("cfe50c0301eccf2413122560655a010091"),
            "source": "advertisement",
            "device_id": "DEVICE-1",
            "received_at": received_at,
        }
    ]


@pytest.mark.asyncio
async def test_drain_waits_for_handler_tasks() -> None:
    release = asyncio.Event()

    async def slow_handler(**_kwargs) -> None:
        await release.wait()

    collector = BLECollector(_settings(), AppState(), slow_handler)
    collector._schedule_frame(_device(), b"\xcf", "advertisement")

    drain = asyncio.create_task(collector._drain_callback_tasks())
    await asyncio.sleep(0.05)
    assert drain.done() is False

    release.set()
    await drain
    assert collector._callback_tasks == set()


@pytest.mark.asyncio
async def test_callback_error_sets_bluetooth_error(caplog) -> None:
    async def failing_handler(**_kwargs) -> None:
        raise RuntimeError("insert failed")

    state = AppState()
    collector = BLECollector(_settings(), state, failing_handler)

    with caplog.at_level(logging.ERROR):
        collector._schedule_frame(_device(), b"\xcf", "advertisement")
        await collector._drain_callback_tasks()
        await asyncio.sleep(0)

    snapshot = state.snapshot()
    assert snapshot["bluetooth"]["status"] == "error"
    assert snapshot["bluetooth"]["last_error"] == "insert failed"
    assert "measurement callback failed" in caplog.text


@pytest.mark.asyncio
async def test_frames_are_ignored_after_stop() -> None:
    captured: list[dict] = []

    async def capture(**kwargs) -> None:
        captured.append(kwargs)

    collector = BLECollector(_settings(), AppState(), capture)
    frame = extract_frame_from_manufacturer_data(
        bytes.fromhex("cfe50c0301eccf2413122560655a0100914a9146")
    )
    assert frame is not None

    await collector.stop()
    collector._schedule_frame(_device(), frame, "advertisement")

    assert collector._callback_tasks == set()
    assert captured == []


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
    collector = _collector(_settings(), state)

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
