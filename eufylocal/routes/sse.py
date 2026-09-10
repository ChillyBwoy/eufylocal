from collections.abc import AsyncIterable

from fastapi import APIRouter
from fastapi.sse import EventSourceResponse, ServerSentEvent

from eufylocal.di import SSEManagerDep
from eufylocal.schemas.sse import ServerSideReadyMessage

router = APIRouter(tags=["events"], prefix="/sse")


@router.get("/", response_class=EventSourceResponse, include_in_schema=False)
async def server_events(sse_manager: SSEManagerDep) -> AsyncIterable[ServerSentEvent]:
    queue = sse_manager.subscribe()

    try:
        yield ServerSentEvent(event="message", data=ServerSideReadyMessage())
        while (message := await queue.get()) is not None:
            yield ServerSentEvent(event="message", data=message)
    finally:
        sse_manager.unsubscribe(queue)
