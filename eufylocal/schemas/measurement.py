from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class MeasurementUnit(StrEnum):
    KG = "kg"
    LB = "lb"


class Measurement(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    measured_at: datetime
    weight: float
    unit: MeasurementUnit
    impedance_ohm: float | None
    device_id: str
    raw_payload_hex: str
