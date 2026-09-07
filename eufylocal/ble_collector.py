from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from eufylocal.config import Settings
from eufylocal.db import Database, Measurement, MeasurementRepository
from eufylocal.parser import extract_frame_from_manufacturer_data, parse_frame
from eufylocal.schemas import BLEStatus
from eufylocal.state import AppState

logger = logging.getLogger(__name__)

SCALE_NAME_TOKEN = "T9146"
SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000fff4-0000-1000-8000-00805f9b34fb"

DEDUP_WINDOW = timedelta(seconds=60)


class BLECollector:
    def __init__(
        self,
        settings: Settings,
        database: Database,
        state: AppState,
    ) -> None:
        self._settings = settings
        self._database = database
        self._state = state
        self._stop_event = asyncio.Event()
        self._client: BleakClient | None = None
        self._last_persisted_at: datetime | None = None
        self._last_persisted_key: tuple[float, float | None] | None = None
        self._persist_lock = asyncio.Lock()
        self._callback_tasks: set[asyncio.Task[None]] = set()

    async def run(self) -> None:
        logger.info("starting BLE collector (transport=%s)", self._settings.transport)
        self._state.set_status(BLEStatus.SCANNING)
        failed = False
        try:
            if self._settings.transport == "gatt":
                await self._run_gatt()
            elif self._settings.transport == "both":
                gatt_task = asyncio.create_task(self._run_gatt())
                try:
                    await self._run_advertisement()
                finally:
                    gatt_task.cancel()
                    await asyncio.gather(gatt_task, return_exceptions=True)
            else:
                await self._run_advertisement()
        except Exception as exc:
            failed = True
            logger.exception("BLE collector failed")
            self._state.set_error(str(exc))
        finally:
            await self._disconnect()
            await self._drain_callback_tasks()
            if not failed:
                self._state.set_status(BLEStatus.IDLE)

    async def stop(self) -> None:
        self._stop_event.set()

    def _matches(self, device: BLEDevice, advertisement: AdvertisementData) -> bool:
        identifier = self._settings.device_identifier
        if identifier:
            return device.address.casefold() == identifier.casefold()
        name = device.name or advertisement.local_name or ""
        return SCALE_NAME_TOKEN in name

    async def _run_advertisement(self) -> None:
        scanner = BleakScanner(detection_callback=self._on_advertisement)
        await scanner.start()
        logger.info("BLE scan started")
        try:
            while not self._stop_event.is_set():
                await asyncio.sleep(0.5)
        finally:
            await scanner.stop()
            logger.info("BLE scan stopped")

    def _on_advertisement(
        self,
        device: BLEDevice,
        advertisement: AdvertisementData,
    ) -> None:
        name = device.name or advertisement.local_name or ""
        logger.debug(
            "advertisement: address=%s name=%r rssi=%s manufacturer=%s",
            device.address,
            name,
            advertisement.rssi,
            {key: value.hex() for key, value in advertisement.manufacturer_data.items()},
        )

        if not self._matches(device, advertisement):
            return

        self._state.set_device(device.address, name)

        for raw in advertisement.manufacturer_data.values():
            frame = extract_frame_from_manufacturer_data(raw)
            if frame is None:
                continue
            logger.info(
                "measurement frame (advertisement) from %s: %s",
                device.address,
                frame.hex(),
            )
            self._schedule_frame(device, frame, "advertisement")

    async def _run_gatt(self) -> None:
        while not self._stop_event.is_set():
            device = await self._find_device()
            if device is None:
                if self._settings.continuous_scan:
                    await asyncio.sleep(2)
                    continue
                await self._stop_event.wait()
                continue

            self._state.set_device(device.address, device.name)
            try:
                await self._connect_and_listen(device)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception("GATT connection failed for %s", device.address)
                self._state.set_error(str(exc))
                await asyncio.sleep(3)

    async def _find_device(self) -> BLEDevice | None:
        timeout = self._settings.scan_timeout

        found: BLEDevice | None = None

        def callback(device: BLEDevice, advertisement: AdvertisementData) -> None:
            nonlocal found
            if found is not None:
                return
            if self._matches(device, advertisement):
                found = device

        scanner = BleakScanner(detection_callback=callback)
        await scanner.start()
        try:
            await asyncio.wait_for(self._stop_event.wait(), timeout=timeout)
        except TimeoutError:
            pass
        finally:
            await scanner.stop()

        return found

    async def _connect_and_listen(self, device: BLEDevice) -> None:
        logger.info("connecting to %s (%s)", device.address, device.name)
        self._state.set_status(BLEStatus.CONNECTING)
        disconnected_event = asyncio.Event()
        client = BleakClient(
            device,
            disconnected_callback=lambda _client: disconnected_event.set(),
        )
        self._client = client
        stop_task: asyncio.Task[bool] | None = None
        disconnected_task: asyncio.Task[bool] | None = None
        try:
            await client.connect()
            self._state.set_error(None)
            self._state.set_status(BLEStatus.CONNECTED)
            logger.info("connected to %s", device.address)
            await client.start_notify(NOTIFY_UUID, self._on_gatt_notification)
            logger.info("subscribed to notifications on %s", NOTIFY_UUID)
            stop_task = asyncio.create_task(self._stop_event.wait())
            disconnected_task = asyncio.create_task(disconnected_event.wait())
            await asyncio.wait(
                (stop_task, disconnected_task),
                return_when=asyncio.FIRST_COMPLETED,
            )
        finally:
            tasks = [task for task in (stop_task, disconnected_task) if task is not None]
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            await self._disconnect()
            self._state.set_status(BLEStatus.SCANNING)

    async def _disconnect(self) -> None:
        if self._client is not None and self._client.is_connected:
            try:
                await self._client.disconnect()
            except Exception:
                logger.exception("error during disconnect")
        self._client = None
        self._state.clear_live_weight()

    def _on_gatt_notification(
        self,
        _sender: BleakGATTCharacteristic,
        data: bytearray,
    ) -> None:
        logger.info("GATT notification: %s", data.hex())
        device_id = self._client.address if self._client else ""
        self._schedule_frame(self._client, data, "gatt", device_id)

    def _schedule_frame(
        self,
        device: BLEDevice | BleakClient | None,
        frame: bytes | bytearray,
        source: str,
        device_id_override: str | None = None,
    ) -> None:
        task = asyncio.create_task(self._handle_frame(device, frame, source, device_id_override))
        self._callback_tasks.add(task)
        task.add_done_callback(self._callback_finished)

    def _callback_finished(self, task: asyncio.Task[None]) -> None:
        self._callback_tasks.discard(task)
        if task.cancelled():
            return
        if error := task.exception():
            logger.error(
                "measurement callback failed",
                exc_info=(type(error), error, error.__traceback__),
            )
            self._state.set_error(str(error))

    async def _drain_callback_tasks(self) -> None:
        if self._callback_tasks:
            await asyncio.gather(*tuple(self._callback_tasks), return_exceptions=True)

    async def _handle_frame(
        self,
        device: BLEDevice | BleakClient | None,
        frame: bytes | bytearray,
        source: str,
        device_id_override: str | None = None,
    ) -> None:
        parsed = parse_frame(frame)
        if parsed is None:
            logger.warning("unparseable frame ignored: %s", bytes(frame).hex())
            return

        logger.info(
            "parsed frame: weight=%.2f kg impedance=%s final=%s unit=%s source=%s",
            parsed.weight_kg,
            parsed.impedance_ohm,
            parsed.is_final,
            parsed.unit,
            source,
        )

        self._state.set_live_weight(parsed.weight_kg, active=not parsed.is_final)

        if parsed.weight_limit_exceeded:
            logger.warning("weight limit exceeded (max weight on scale)")
            return

        if not parsed.is_final:
            logger.debug("ignoring non-final (unstable) frame")
            return

        device_id = device_id_override or (
            getattr(device, "address", "") or self._settings.device_identifier or "unknown"
        )
        measurement = Measurement.now(
            weight_kg=parsed.weight_kg,
            impedance_ohm=parsed.impedance_ohm,
            device_id=device_id,
            source=source,
            raw_payload_hex=bytes(frame).hex(),
        )

        async with self._persist_lock:
            if self._is_duplicate(measurement):
                logger.debug("duplicate final measurement skipped")
                return

            async with self._database.session() as session:
                await MeasurementRepository(session).insert(measurement)
            self._state.set_last_measurement(measurement)
            self._last_persisted_at = measurement.measured_at
            self._last_persisted_key = (measurement.weight_kg, measurement.impedance_ohm)
        logger.info(
            "stored measurement: weight=%.2f kg impedance=%s source=%s",
            measurement.weight_kg,
            measurement.impedance_ohm,
            source,
        )

    def _is_duplicate(self, measurement: Measurement) -> bool:
        if self._last_persisted_at is None or self._last_persisted_key is None:
            return False
        key = (measurement.weight_kg, measurement.impedance_ohm)
        if key != self._last_persisted_key:
            return False
        return measurement.measured_at - self._last_persisted_at < DEDUP_WINDOW


async def scan_and_print(
    settings: Settings,
    duration: float,
    repeat_payloads: bool = False,
) -> None:
    seen: set[str] = set()

    def callback(device: BLEDevice, advertisement: AdvertisementData) -> None:
        if repeat_payloads:
            identifier = settings.device_identifier
            name = device.name or advertisement.local_name or ""
            if identifier and device.address.casefold() != identifier.casefold():
                return
            if not identifier and SCALE_NAME_TOKEN not in name:
                return
        elif device.address in seen:
            return
        else:
            seen.add(device.address)
        name = device.name or advertisement.local_name or ""
        logger.info(
            "device found: address=%s name=%r rssi=%s manufacturer=%s",
            device.address,
            name,
            advertisement.rssi,
            {key: value.hex() for key, value in advertisement.manufacturer_data.items()},
        )

    scanner = BleakScanner(detection_callback=callback)
    await scanner.start()
    await asyncio.sleep(duration)
    await scanner.stop()
