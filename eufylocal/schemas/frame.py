from dataclasses import dataclass

from eufylocal.schemas.measurement import MeasurementUnit


@dataclass(frozen=True)
class ParsedFrame:
    weight: float
    impedance_ohm: float | None
    weight_limit_exceeded: bool
    unit: MeasurementUnit
    is_final: bool
    raw: str
