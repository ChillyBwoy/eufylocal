import asyncio

from alembic import command
from sqlalchemy import inspect

from eufylocal.db import Database
from eufylocal.db.migration import migration_config


def test_upgrade_and_downgrade(tmp_path) -> None:
    database_path = tmp_path / "migrations.db"
    config = migration_config(database_path)

    command.upgrade(config, "head")

    async def inspect_schema() -> tuple[list[str], list[dict], list[dict]]:
        database = Database(database_path)
        async with database.engine.connect() as connection:
            schema = await connection.run_sync(
                lambda sync_connection: (
                    inspect(sync_connection).get_table_names(),
                    inspect(sync_connection).get_columns("measurements"),
                    inspect(sync_connection).get_indexes("measurements"),
                )
            )
        await database.close()
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
    assert {index["name"] for index in indexes} == {"idx_measurements_measured_at"}

    command.downgrade(config, "base")

    async def table_names() -> list[str]:
        database = Database(database_path)
        async with database.engine.connect() as connection:
            tables = await connection.run_sync(
                lambda sync_connection: inspect(sync_connection).get_table_names()
            )
        await database.close()
        return tables

    assert "measurements" not in asyncio.run(table_names())
