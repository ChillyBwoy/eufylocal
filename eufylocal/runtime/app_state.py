from __future__ import annotations

import threading
import time
from collections.abc import Callable
from datetime import datetime

from eufylocal.schemas import BLEStatus, BluetoothStatus, StatusEvent

LIVE_WEIGHT_TTL_SECONDS = 10.0


class AppState:
    def __init__(
        self,
        *,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._lock = threading.Lock()
        self._monotonic = monotonic
        self._live_weight_expires_at: float | None = None
        self._current = BluetoothStatus(
            status=BLEStatus.IDLE,
            device_id=None,
            device_name=None,
            last_error=None,
            live_weight_kg=None,
            live_weight_active=False,
            last_received_at=None,
        )

    def apply(
        self,
        event: StatusEvent,
        *,
        device_id: str | None = None,
        device_name: str | None = None,
        message: str | None = None,
        received_at: datetime | None = None,
        weight_kg: float | None = None,
        is_final: bool = False,
    ) -> None:
        with self._lock:
            if event is StatusEvent.SCAN_STARTED:
                self._update(status=BLEStatus.SCANNING)
            elif event is StatusEvent.DEVICE_DISCOVERED:
                self._update(device_id=device_id, device_name=device_name)
            elif event is StatusEvent.CONNECTION_STARTED:
                self._update(status=BLEStatus.CONNECTING)
            elif event is StatusEvent.CONNECTION_ESTABLISHED:
                self._update(status=BLEStatus.CONNECTED, last_error=None)
            elif event is StatusEvent.CONNECTION_LOST:
                self._clear_live_weight(status=BLEStatus.SCANNING)
            elif event is StatusEvent.COLLECTOR_STOPPED:
                self._clear_live_weight(status=BLEStatus.IDLE)
            elif event is StatusEvent.PROCESSING_FAILED:
                self._clear_live_weight(status=BLEStatus.ERROR, last_error=message)
            elif event is StatusEvent.READING_RECEIVED:
                if received_at is None or weight_kg is None:
                    raise ValueError("reading event requires received_at and weight_kg")
                self._live_weight_expires_at = (
                    None if is_final else self._monotonic() + LIVE_WEIGHT_TTL_SECONDS
                )
                self._update(
                    live_weight_kg=weight_kg,
                    live_weight_active=not is_final,
                    last_received_at=received_at,
                )

    def current(self) -> BluetoothStatus:
        with self._lock:
            if (
                self._current.live_weight_active
                and self._live_weight_expires_at is not None
                and self._monotonic() >= self._live_weight_expires_at
            ):
                return self._current.model_copy(
                    update={"live_weight_kg": None, "live_weight_active": False}
                )
            return self._current

    def _clear_live_weight(self, **updates: object) -> None:
        self._live_weight_expires_at = None
        self._update(live_weight_kg=None, live_weight_active=False, **updates)

    def _update(self, **updates: object) -> None:
        self._current = self._current.model_copy(update=updates)
