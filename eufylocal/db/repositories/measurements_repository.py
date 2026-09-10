from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eufylocal.db.models import MeasurementModel
from eufylocal.schemas.measurement import MeasurementUnit


class MeasurementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert(
        self,
        weight: float,
        unit: MeasurementUnit,
        impedance_ohm: float,
        device_id: str,
        raw_data: str,
    ) -> None:
        measurement = MeasurementModel(
            measured_at=datetime.now(UTC),
            weight=weight,
            unit=unit,
            impedance_ohm=impedance_ohm,
            device_id=device_id,
            raw_data=raw_data,
        )
        self.session.add(measurement)

        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def list(
        self,
        limit: int = 50,
    ) -> list[MeasurementModel]:
        stmt = select(MeasurementModel)
        stmt = stmt.order_by(
            MeasurementModel.measured_at.desc(),
            MeasurementModel.id.desc(),
        ).limit(limit)
        return list(await self.session.scalars(stmt))

    async def latest(self) -> MeasurementModel | None:
        stmt = select(MeasurementModel)
        stmt = stmt.order_by(
            MeasurementModel.measured_at.desc(),
            MeasurementModel.id.desc(),
        ).limit(1)
        return await self.session.scalar(stmt)
