from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eufylocal.db.models import Measurement


class MeasurementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert(self, measurement: Measurement) -> None:
        self.session.add(measurement)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def list(self, limit: int = 50) -> list[Measurement]:
        statement = (
            select(Measurement)
            .order_by(Measurement.measured_at.desc(), Measurement.id.desc())
            .limit(limit)
        )
        return list(await self.session.scalars(statement))

    async def latest(self) -> Measurement | None:
        statement = (
            select(Measurement)
            .order_by(Measurement.measured_at.desc(), Measurement.id.desc())
            .limit(1)
        )
        return await self.session.scalar(statement)
