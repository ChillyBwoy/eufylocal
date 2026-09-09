import uuid
from collections.abc import AsyncIterator, Iterator

import pytest
import pytest_asyncio
from sqlalchemy import URL, create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from eufylocal.config import Settings
from eufylocal.db.migration import upgrade_database

test_settings = Settings()
TEST_ADMIN_DB_URL = URL.create(
    "postgresql+psycopg",
    username=test_settings.db_user,
    password=test_settings.db_password,
    host=test_settings.db_host,
    port=test_settings.db_port,
    database="postgres",
)


@pytest.fixture
def database_url() -> Iterator[str]:
    database_name = f"eufylocal_test_{uuid.uuid4().hex}"
    admin_engine = create_engine(TEST_ADMIN_DB_URL, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        connection.exec_driver_sql(f'CREATE DATABASE "{database_name}"')

    test_url = TEST_ADMIN_DB_URL.set(database=database_name)
    try:
        yield test_url.render_as_string(hide_password=False)
    finally:
        with admin_engine.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :database_name AND pid <> pg_backend_pid()"
                ),
                {"database_name": database_name},
            )
            connection.exec_driver_sql(f'DROP DATABASE "{database_name}"')
        admin_engine.dispose()


@pytest_asyncio.fixture
async def session_factory(database_url: str) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    upgrade_database(database_url)
    engine = create_async_engine(database_url, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()
