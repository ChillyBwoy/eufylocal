from __future__ import annotations

from alembic import context
from sqlalchemy import URL, create_engine, make_url
from sqlalchemy.pool import NullPool

from eufylocal.config import Settings
from eufylocal.db.models import BaseModel

config = context.config
target_metadata = BaseModel.metadata


def _database_url() -> URL:
    configured_url = config.attributes.get("db_url")
    url = make_url(configured_url if isinstance(configured_url, str) else Settings().db_url)
    if url.drivername == "sqlite+aiosqlite":
        return url.set(drivername="sqlite+pysqlite")
    return url


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
