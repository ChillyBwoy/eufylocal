from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import URL, event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool


def database_url(path: Path) -> URL:
    return URL.create("sqlite+aiosqlite", database=str(path))


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        if path != Path(":memory:"):
            path.parent.mkdir(parents=True, exist_ok=True)

        engine_options: dict[str, object] = {
            "connect_args": {"check_same_thread": False},
        }
        if path == Path(":memory:"):
            engine_options["poolclass"] = StaticPool

        self.engine: AsyncEngine = create_async_engine(database_url(path), **engine_options)
        self._sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        event.listen(self.engine.sync_engine, "connect", self._set_sqlite_pragmas)

    @staticmethod
    def _set_sqlite_pragmas(dbapi_connection: Any, _connection_record: object) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
        finally:
            cursor.close()

    def session(self) -> AsyncSession:
        return self._sessions()

    async def close(self) -> None:
        await self.engine.dispose()
