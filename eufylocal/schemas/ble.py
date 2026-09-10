from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class BLEStatus(StrEnum):
    IDLE = "idle"
    SCANNING = "scanning"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class BluetoothStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: BLEStatus
    device_id: str | None
    device_name: str | None
    last_error: str | None
    live_weight: float | None
    live_weight_active: bool
    last_received_at: datetime | None
