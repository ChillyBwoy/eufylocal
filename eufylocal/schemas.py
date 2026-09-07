from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict


class BLEStatus(StrEnum):
    IDLE = "idle"
    SCANNING = "scanning"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class Measurement(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    measured_at: datetime
    weight_kg: float
    impedance_ohm: float | None
    device_id: str
    source: Literal["advertisement", "gatt"]
    raw_payload_hex: str


class BluetoothStatus(BaseModel):
    status: BLEStatus
    device_id: str | None
    device_name: str | None
    last_error: str | None
    live_weight_kg: float | None
    live_weight_active: bool


class Status(BaseModel):
    bluetooth: BluetoothStatus
    last_measurement: Measurement | None
    server_time: datetime
