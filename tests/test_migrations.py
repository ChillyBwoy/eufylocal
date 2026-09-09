import asyncio

from alembic import command
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from eufylocal.db.migration import migration_config


def test_upgrade_and_downgrade(database_url: str) -> None:
    config = migration_config(database_url)

    command.upgrade(config, "head")

    async def inspect_schema() -> tuple[list[str], list[dict], list[dict]]:
        engine = create_async_engine(database_url)
        async with engine.connect() as connection:
            schema = await connection.run_sync(
                lambda sync_connection: (
                    inspect(sync_connection).get_table_names(),
                    inspect(sync_connection).get_columns("measurements"),
                    inspect(sync_connection).get_indexes("measurements"),
                )
            )
        await engine.dispose()
        return schema

    tables, columns, indexes = asyncio.run(inspect_schema())
    assert "measurements" in tables
    assert "alembic_version" in tables
    assert {column["name"] for column in columns} == {
        "id",
        "measured_at",
        "weight_kg",
        "impedance_ohm",
        "device_id",
        "source",
        "raw_payload_hex",
    }
    assert {index["name"] for index in indexes} == {"idx_measurements_measured_at_id"}

    command.downgrade(config, "base")

    async def table_names() -> list[str]:
        engine = create_async_engine(database_url)
        async with engine.connect() as connection:
            tables = await connection.run_sync(
                lambda sync_connection: inspect(sync_connection).get_table_names()
            )
        await engine.dispose()
        return tables

    assert "measurements" not in asyncio.run(table_names())
