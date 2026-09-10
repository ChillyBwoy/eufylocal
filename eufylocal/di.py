from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from eufylocal.db import session as db_session
from eufylocal.db.repositories import MeasurementRepository
from eufylocal.sse_manager import SSEManager, sse_manager


async def get_db() -> AsyncIterator[AsyncSession]:
    async with db_session.AsyncSessionLocal() as session:
        yield session


def get_sse_manager() -> SSEManager:
    return sse_manager


SSEManagerDep = Annotated[SSEManager, Depends(get_sse_manager)]


def get_measurement_repo(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MeasurementRepository:
    return MeasurementRepository(db)


MeasurementRepositoryDep = Annotated[
    MeasurementRepository,
    Depends(get_measurement_repo),
]
