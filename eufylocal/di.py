from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from eufylocal.db import MeasurementRepository
from eufylocal.db import session as db_session
from eufylocal.runtime import AppState, EventBus, Runtime


async def get_db() -> AsyncIterator[AsyncSession]:
    async with db_session.AsyncSessionLocal() as session:
        yield session


def get_app_state(request: Request) -> AppState:
    return cast(Runtime, request.app.state.runtime).state


def get_event_bus(request: Request) -> EventBus:
    return cast(Runtime, request.app.state.runtime).events


def get_measurement_repo(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MeasurementRepository:
    return MeasurementRepository(db)


MeasurementRepositoryDep = Annotated[
    MeasurementRepository,
    Depends(get_measurement_repo),
]

AppStateDep = Annotated[AppState, Depends(get_app_state)]
EventBusDep = Annotated[EventBus, Depends(get_event_bus)]
