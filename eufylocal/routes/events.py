from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from eufylocal.di import EventBusDep
from eufylocal.runtime import EventBus

KEEPALIVE_SECONDS = 15.0

router = APIRouter(prefix="/api", tags=["events"])


async def event_stream(
    events: EventBus,
    *,
    keepalive_seconds: float = KEEPALIVE_SECONDS,
) -> AsyncIterator[str]:
    queue = events.subscribe()
    try:
        yield "event: ready\ndata: {}\n\n"
        while True:
            try:
                await asyncio.wait_for(queue.get(), timeout=keepalive_seconds)
            except TimeoutError:
                yield ": keepalive\n\n"
            else:
                yield "event: refresh\ndata: {}\n\n"
    finally:
        events.unsubscribe(queue)


@router.get(
    "/events",
    include_in_schema=False,
)
async def server_events(events: EventBusDep) -> StreamingResponse:
    return StreamingResponse(
        event_stream(events),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
