import asyncio

from eufylocal.schemas.sse import ServerSideMessage


class SSEManager:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[ServerSideMessage | None]] = set()
        self._closed = False

    def subscribe(self) -> asyncio.Queue[ServerSideMessage | None]:
        queue: asyncio.Queue[ServerSideMessage | None] = asyncio.Queue()
        self._subscribers.add(queue)
        if self._closed:
            queue.put_nowait(None)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[ServerSideMessage | None]) -> None:
        self._subscribers.discard(queue)

    def publish(self, message: ServerSideMessage) -> None:
        for queue in self._subscribers:
            queue.put_nowait(message)

    def close(self) -> None:
        self._closed = True
        for queue in self._subscribers:
            queue.put_nowait(None)


sse_manager = SSEManager()
