from __future__ import annotations

from pathlib import Path

from alembic import context
from sqlalchemy import URL, create_engine
from sqlalchemy.pool import NullPool

from eufylocal.config import Settings
from eufylocal.db.models import BaseModel

config = context.config
target_metadata = BaseModel.metadata


def _database_path() -> Path:
    configured_path = config.attributes.get("database_path")
    return configured_path if isinstance(configured_path, Path) else Settings().database_path


def _database_url() -> URL:
    return URL.create("sqlite+pysqlite", database=str(_database_path()))


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url().render_as_string(hide_password=False),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        _database_url(),
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
