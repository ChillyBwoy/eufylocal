from __future__ import annotations

import threading
import time
from datetime import UTC, datetime

from eufylocal.models import BLEStatus, Measurement

LIVE_WEIGHT_TTL_SECONDS = 10.0


class AppState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._status = BLEStatus.IDLE
        self._device_name: str | None = None
        self._device_id: str | None = None
        self._last_error: str | None = None
        self._live_weight_kg: float | None = None
        self._live_weight_active = False
        self._live_weight_updated_at: float | None = None
        self._last_measurement: Measurement | None = None

    def set_status(self, status: BLEStatus) -> None:
        with self._lock:
            self._status = status

    def set_device(self, device_id: str | None, device_name: str | None = None) -> None:
        with self._lock:
            self._device_id = device_id
            if device_name is not None:
                self._device_name = device_name

    def set_error(self, message: str | None) -> None:
        with self._lock:
            self._last_error = message
            if message is not None:
                self._status = BLEStatus.ERROR

    def set_live_weight(self, weight_kg: float | None, active: bool = True) -> None:
        with self._lock:
            self._live_weight_kg = weight_kg
            self._live_weight_active = active
            self._live_weight_updated_at = time.monotonic() if active else None

    def clear_live_weight(self) -> None:
        with self._lock:
            self._live_weight_kg = None
            self._live_weight_active = False
            self._live_weight_updated_at = None

    def set_last_measurement(self, measurement: Measurement) -> None:
        with self._lock:
            self._last_measurement = measurement
            self._live_weight_kg = measurement.weight_kg
            self._live_weight_active = False
            self._live_weight_updated_at = None

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            if (
                self._live_weight_active
                and self._live_weight_updated_at is not None
                and time.monotonic() - self._live_weight_updated_at >= LIVE_WEIGHT_TTL_SECONDS
            ):
                self._live_weight_kg = None
                self._live_weight_active = False
                self._live_weight_updated_at = None
            return {
                "bluetooth": {
                    "status": self._status.value,
                    "device_id": self._device_id,
                    "device_name": self._device_name,
                    "last_error": self._last_error,
                    "live_weight_kg": self._live_weight_kg,
                    "live_weight_active": self._live_weight_active,
                },
                "last_measurement": (
                    self._last_measurement.to_dict() if self._last_measurement else None
                ),
                "server_time": datetime.now(UTC).isoformat(),
            }
