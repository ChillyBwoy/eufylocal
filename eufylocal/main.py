from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from types import FrameType

import uvicorn
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles

from eufylocal.config import settings
from eufylocal.router import api_router
from eufylocal.scanner import scan

STATIC_DIR = Path(__file__).parent / "static"


async def consume_frames() -> None:
    async for frame in scan():
        print(frame, flush=True)


def custom_generate_unique_id(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"


@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncGenerator[None]:
    collector_task = asyncio.create_task(consume_frames())
    try:
        yield
    finally:
        collector_task.cancel()
        await asyncio.gather(collector_task, return_exceptions=True)


app = FastAPI(
    title="eufylocal",
    debug=settings.debug,
    lifespan=lifespan,
    generate_unique_id_function=custom_generate_unique_id,
)
app.include_router(api_router)

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")


class Server(uvicorn.Server):
    def handle_exit(self, sig: int, frame: FrameType | None) -> None:
        runtime = getattr(app.state, "runtime", None)
        if runtime is not None:
            runtime.close()
        super().handle_exit(sig, frame)


def run() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    config = uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        log_level=logging.INFO,
        timeout_graceful_shutdown=1,
    )

    with suppress(KeyboardInterrupt):
        Server(config).run()
