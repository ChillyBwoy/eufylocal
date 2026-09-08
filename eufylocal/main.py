from __future__ import annotations

import argparse
import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles

from eufylocal.ble_collector import scan_and_print
from eufylocal.config import settings
from eufylocal.db import MeasurementRepository
from eufylocal.db import session as db_session
from eufylocal.db.migration import upgrade_database
from eufylocal.routes.info import router as info_router
from eufylocal.routes.measurements import router as measurements_router
from eufylocal.runtime import create_runtime

STATIC_DIR = Path(__file__).parent / "static"


def custom_generate_unique_id(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    if settings.auto_migrate:
        await asyncio.to_thread(upgrade_database, settings.db_url)
    try:
        async with db_session.AsyncSessionLocal() as writer_session:
            runtime, collector = create_runtime(
                MeasurementRepository(writer_session),
            )
            application.state.runtime = runtime
            application.state.collector = collector
            collector_task = asyncio.create_task(collector.run()) if settings.ble_enabled else None
            try:
                yield
            finally:
                if collector_task is not None:
                    await collector.stop()
                    collector_task.cancel()
                    await asyncio.gather(collector_task, return_exceptions=True)
    finally:
        await db_session.engine.dispose()


app = FastAPI(
    title="eufylocal",
    lifespan=lifespan,
    generate_unique_id_function=custom_generate_unique_id,
)
app.include_router(info_router)
app.include_router(measurements_router)


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eufylocal",
        description="Local BLE bridge for the eufy Smart Scale C1 (T9146)",
    )
    parser.add_argument("--log-level", help="override logging level")
    subparsers = parser.add_subparsers(dest="command")

    serve = subparsers.add_parser("serve", help="run the local server (default)")
    serve.add_argument("--host", help="bind address (default 127.0.0.1)")
    serve.add_argument("--port", type=int, help="bind port (default 8000)")

    scan = subparsers.add_parser("scan", help="scan BLE devices once and exit")
    scan.add_argument("--timeout", type=float, default=10.0)

    dump = subparsers.add_parser("dump", help="continuously print raw BLE payloads (diagnostics)")
    dump.add_argument("--timeout", type=float, default=30.0)
    return parser


def run(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    _configure_logging(args.log_level or settings.log_level)
    command = args.command or "serve"

    if command == "scan":
        asyncio.run(scan_and_print(args.timeout))
        return
    if command == "dump":
        asyncio.run(scan_and_print(args.timeout, repeat_payloads=True))
        return

    uvicorn.run(
        app,
        host=args.host or settings.host,
        port=args.port or settings.port,
        log_level=(args.log_level or settings.log_level).lower(),
    )
