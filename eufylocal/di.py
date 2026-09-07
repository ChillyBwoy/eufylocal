from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from eufylocal.db import Database, MeasurementRepository


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    database = cast(Database, request.app.state.database)
    async with database.session() as session:
        yield session


def get_measurement_repo(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MeasurementRepository:
    return MeasurementRepository(db)


MeasurementRepositoryDep = Annotated[
    MeasurementRepository,
    Depends(get_measurement_repo),
]
