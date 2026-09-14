from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from eufylocal.schemas.measurement import MeasurementUnit


class BaseModel(DeclarativeBase):
    pass


class UserModel(BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    color: Mapped[str] = mapped_column(Text, nullable=False)

    measurements: Mapped[list[MeasurementModel]] = relationship(
        back_populates="user",
        passive_deletes=True,
    )


class MeasurementModel(BaseModel):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[MeasurementUnit] = mapped_column(Enum(MeasurementUnit), nullable=False)
    impedance_ohm: Mapped[float | None] = mapped_column(Float)
    raw_data: Mapped[str] = mapped_column(Text, nullable=False)

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", name="fk_measurements_user_id_users", ondelete="SET NULL"),
        nullable=True,
    )
    user: Mapped[UserModel | None] = relationship(back_populates="measurements")

    __table_args__ = (
        CheckConstraint("weight > 0", name="ck_measurements_weight_positive"),
        CheckConstraint(
            "impedance_ohm IS NULL OR impedance_ohm > 0",
            name="ck_measurements_impedance_positive",
        ),
        Index("ix_measurements_measured_at_id", measured_at.desc(), id.desc()),
        Index(
            "ix_measurements_user_id_measured_at_id",
            user_id,
            measured_at.desc(),
            id.desc(),
        ),
    )
