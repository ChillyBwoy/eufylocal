from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class BLEStatus(StrEnum):
    IDLE = "idle"
    SCANNING = "scanning"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass(frozen=True)
class Measurement:
    measured_at: datetime
    weight_kg: float
    impedance_ohm: float | None
    device_id: str
    source: str
    raw_payload_hex: str

    @classmethod
    def now(
        cls,
        weight_kg: float,
        impedance_ohm: float | None,
        device_id: str,
        source: str,
        raw_payload_hex: str,
    ) -> Measurement:
        return cls(
            measured_at=datetime.now(UTC),
            weight_kg=round(weight_kg, 2),
            impedance_ohm=round(impedance_ohm, 1) if impedance_ohm is not None else None,
            device_id=device_id,
            source=source,
            raw_payload_hex=raw_payload_hex,
        )

    def to_dict(self) -> dict[str, datetime | float | str | None]:
        return {
            "measured_at": self.measured_at.isoformat(),
            "weight_kg": self.weight_kg,
            "impedance_ohm": self.impedance_ohm,
            "device_id": self.device_id,
            "source": self.source,
            "raw_payload_hex": self.raw_payload_hex,
        }
