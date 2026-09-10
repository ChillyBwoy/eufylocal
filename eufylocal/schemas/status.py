from datetime import datetime

from pydantic import BaseModel

from eufylocal.schemas.ble import BluetoothStatus
from eufylocal.schemas.measurement import Measurement


class Status(BaseModel):
    bluetooth: BluetoothStatus
    last_measurement: Measurement | None
    server_time: datetime
