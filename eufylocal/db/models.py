from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Identity, Index, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BaseModel(DeclarativeBase):
    pass


class MeasurementModel(BaseModel):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    impedance_ohm: Mapped[float | None] = mapped_column(Float)
    device_id: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload_hex: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (Index("idx_measurements_measured_at_id", measured_at.desc(), id.desc()),)
