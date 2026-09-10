from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from eufylocal.db import session as db_session
from eufylocal.db.repositories import MeasurementRepository
from eufylocal.sse import SSE


async def get_db() -> AsyncIterator[AsyncSession]:
    async with db_session.AsyncSessionLocal() as session:
        yield session


def get_sse() -> SSE:
    return SSE()


SSEDep = Annotated[SSE, Depends(get_sse)]


def get_measurement_repo(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MeasurementRepository:
    return MeasurementRepository(db)


MeasurementRepositoryDep = Annotated[
    MeasurementRepository,
    Depends(get_measurement_repo),
]
