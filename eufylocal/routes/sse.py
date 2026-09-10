from __future__ import annotations

from collections.abc import AsyncIterable

from fastapi import APIRouter
from fastapi.sse import EventSourceResponse, ServerSentEvent

from eufylocal.di import SSEDep
from eufylocal.schemas.sse import ServerSideReadyMessage

router = APIRouter(tags=["events"], prefix="/sse")


@router.get("/", response_class=EventSourceResponse, include_in_schema=False)
async def server_events(sse: SSEDep) -> AsyncIterable[ServerSentEvent]:
    queue = sse.subscribe()

    try:
        yield ServerSentEvent(event="message", data=ServerSideReadyMessage())
    finally:
        sse.unsubscribe(queue)
