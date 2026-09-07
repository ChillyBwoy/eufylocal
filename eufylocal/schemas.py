from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from eufylocal.models import BLEStatus


class MeasurementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    measured_at: datetime
    weight_kg: float
    impedance_ohm: float | None
    device_id: str
    source: Literal["advertisement", "gatt"]
    raw_payload_hex: str


class MeasurementsResponse(BaseModel):
    measurements: list[MeasurementResponse]


class BluetoothStatusResponse(BaseModel):
    status: BLEStatus
    device_id: str | None
    device_name: str | None
    last_error: str | None
    live_weight_kg: float | None
    live_weight_active: bool


class StatusResponse(BaseModel):
    bluetooth: BluetoothStatusResponse
    last_measurement: MeasurementResponse | None
    server_time: datetime
