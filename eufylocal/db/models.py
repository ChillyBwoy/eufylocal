from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Float, Index, Integer, Text
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator[datetime]):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("measured_at must include timezone information")
        return value.astimezone(UTC).isoformat()

    def process_result_value(self, value: str | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        return datetime.fromisoformat(value).astimezone(UTC)


class BaseModel(DeclarativeBase):
    pass


class MeasurementModel(BaseModel):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    measured_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    impedance_ohm: Mapped[float | None] = mapped_column(Float)
    device_id: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload_hex: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("idx_measurements_measured_at", measured_at.desc()),
        {"sqlite_autoincrement": True},
    )

    @classmethod
    def from_received(
        cls,
        received_at: datetime,
        weight_kg: float,
        impedance_ohm: float | None,
        device_id: str,
        source: str,
        raw_payload_hex: str,
    ) -> MeasurementModel:
        return cls(
            measured_at=received_at,
            weight_kg=round(weight_kg, 2),
            impedance_ohm=round(impedance_ohm, 1) if impedance_ohm is not None else None,
            device_id=device_id,
            source=source,
            raw_payload_hex=raw_payload_hex,
        )
