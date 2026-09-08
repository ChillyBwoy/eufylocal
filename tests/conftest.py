from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from eufylocal.db.migration import upgrade_database


@pytest_asyncio.fixture
async def session_factory(tmp_path) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    db_url = URL.create(
        "sqlite+aiosqlite",
        database=str(tmp_path / "test.db"),
    ).render_as_string(hide_password=False)
    upgrade_database(db_url)
    engine = create_async_engine(db_url, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()
