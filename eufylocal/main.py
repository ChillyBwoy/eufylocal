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
from eufylocal.db.repositories import MeasurementRepository
from eufylocal.db.session import AsyncSessionLocal
from eufylocal.router import api_router
from eufylocal.scanner import scan
from eufylocal.schemas.sse import ServerSideRefreshMessage, ServerSideStatusMessage
from eufylocal.sse_manager import sse_manager

STATIC_DIR = Path(__file__).parent / "static"

logger = logging.getLogger(__name__)


async def consume_frames(measurement_repo: MeasurementRepository) -> None:
    waiting_for_next_weighing = False

    async for frame in scan():
        if waiting_for_next_weighing:
            if frame.is_final:
                continue
            waiting_for_next_weighing = False

        logger.info(
            "weight=%.2f unit=%s impedance=%s weight_limit_exceeded=%s is_final=%s raw=%s",
            frame.weight,
            frame.unit,
            f"{frame.impedance_ohm:.2f}" if frame.impedance_ohm is not None else "n/a",
            frame.weight_limit_exceeded,
            frame.is_final,
            frame.raw,
        )

        message = ServerSideStatusMessage(
            impedance_ohm=frame.impedance_ohm,
            weight=frame.weight,
            unit=frame.unit,
        )

        sse_manager.publish(message)

        waiting_for_next_weighing = frame.is_final
        if frame.is_final:
            await measurement_repo.insert(
                weight=frame.weight,
                unit=frame.unit,
                impedance_ohm=frame.impedance_ohm,
                raw_data=frame.raw,
            )
            sse_manager.publish(ServerSideRefreshMessage())


def custom_generate_unique_id(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"


@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncGenerator[None]:
    async with AsyncSessionLocal() as db:
        measurement_repo = MeasurementRepository(db)
        collector_task = asyncio.create_task(consume_frames(measurement_repo=measurement_repo))
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
        sse_manager.close()
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
