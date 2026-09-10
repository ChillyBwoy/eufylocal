from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    Identity,
    Index,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from eufylocal.schemas.measurement import MeasurementUnit


class BaseModel(DeclarativeBase):
    pass


class MeasurementModel(BaseModel):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[MeasurementUnit] = mapped_column(Enum(MeasurementUnit), nullable=False)
    impedance_ohm: Mapped[float | None] = mapped_column(Float)
    raw_data: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        CheckConstraint("weight > 0", name="ck_measurements_weight_positive"),
        CheckConstraint(
            "impedance_ohm IS NULL OR impedance_ohm > 0",
            name="ck_measurements_impedance_positive",
        ),
        Index("ix_measurements_measured_at_id", measured_at.desc(), id.desc()),
    )
