import asyncio
from datetime import datetime

from eufylocal.ble_collector import BLECollector
from eufylocal.db import MeasurementRepository
from eufylocal.runtime.app_state import LIVE_WEIGHT_TTL_SECONDS, AppState
from eufylocal.runtime.events import EventBus
from eufylocal.runtime.measurement_handler import MeasurementHandler
from eufylocal.runtime.measurement_writer import MeasurementWriter
from eufylocal.schemas import BluetoothStatus, FinalMeasurementReceived, StatusEvent


class Runtime:
    def __init__(self, measurement_repo: MeasurementRepository) -> None:
        self.state = AppState()
        self.events = EventBus()
        self._last_published_status = self._status_key()
        self._expiry_handle: asyncio.TimerHandle | None = None
        self._writer = MeasurementWriter(measurement_repo)
        handler = MeasurementHandler(self.apply_status, self.write_measurement)
        self.collector = BLECollector(self.apply_status, handler.handle_frame)

    def apply_status(
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
        self.state.apply(
            event,
            device_id=device_id,
            device_name=device_name,
            message=message,
            received_at=received_at,
            weight_kg=weight_kg,
            is_final=is_final,
        )
        current = self.state.current()

        if event is StatusEvent.READING_RECEIVED and current.live_weight_active:
            self._cancel_expiry()
            self._expiry_handle = asyncio.get_running_loop().call_later(
                LIVE_WEIGHT_TTL_SECONDS,
                self._publish_expiry,
            )
        elif not current.live_weight_active:
            self._cancel_expiry()

        status_key = self._status_key()
        if status_key != self._last_published_status:
            self._last_published_status = status_key
            self.events.publish()

    async def write_measurement(self, event: FinalMeasurementReceived) -> None:
        if await self._writer(event):
            self.events.publish()

    def close(self) -> None:
        self._cancel_expiry()

    def _cancel_expiry(self) -> None:
        if self._expiry_handle is not None:
            self._expiry_handle.cancel()
            self._expiry_handle = None

    def _publish_expiry(self) -> None:
        self._expiry_handle = None
        status_key = self._status_key()
        if status_key != self._last_published_status:
            self._last_published_status = status_key
            self.events.publish()

    def _status_key(self) -> BluetoothStatus:
        return self.state.current().model_copy(update={"last_received_at": None})
