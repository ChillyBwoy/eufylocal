from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from eufylocal.config import settings
from eufylocal.db.models import BaseModel

config = context.config
target_metadata = BaseModel.metadata


config.set_main_option("sqlalchemy.url", str(settings.db_url))


def run_migrations_offline() -> None:
    context.configure(
        url=str(settings.db_url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        str(settings.db_url),
        poolclass=NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
