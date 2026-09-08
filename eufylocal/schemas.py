from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

type MeasurementSource = Literal["advertisement", "gatt"]


class BLEStatus(StrEnum):
    IDLE = "idle"
    SCANNING = "scanning"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class StatusEvent(StrEnum):
    SCAN_STARTED = "scan_started"
    DEVICE_DISCOVERED = "device_discovered"
    CONNECTION_STARTED = "connection_started"
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_LOST = "connection_lost"
    COLLECTOR_STOPPED = "collector_stopped"
    PROCESSING_FAILED = "processing_failed"
    READING_RECEIVED = "reading_received"


@dataclass(frozen=True, slots=True)
class FinalMeasurementReceived:
    measured_at: datetime
    weight_kg: float
    impedance_ohm: float | None
    device_id: str
    source: MeasurementSource
    raw_payload_hex: str


class Measurement(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    measured_at: datetime
    weight_kg: float
    impedance_ohm: float | None
    device_id: str
    source: Literal["advertisement", "gatt"]
    raw_payload_hex: str


class BluetoothStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: BLEStatus
    device_id: str | None
    device_name: str | None
    last_error: str | None
    live_weight_kg: float | None
    live_weight_active: bool
    last_received_at: datetime | None


class Status(BaseModel):
    bluetooth: BluetoothStatus
    last_measurement: Measurement | None
    server_time: datetime
