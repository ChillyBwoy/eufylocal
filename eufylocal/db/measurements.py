from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eufylocal.db.models import MeasurementModel


class MeasurementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert(self, measurement: MeasurementModel) -> None:
        self.session.add(measurement)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def list(self, limit: int = 50) -> list[MeasurementModel]:
        stmt = (
            select(MeasurementModel)
            .order_by(MeasurementModel.measured_at.desc(), MeasurementModel.id.desc())
            .limit(limit)
        )
        return list(await self.session.scalars(stmt))

    async def latest(self) -> MeasurementModel | None:
        stmt = select(MeasurementModel).order_by(MeasurementModel.id.desc()).limit(1)
        return await self.session.scalar(stmt)
