from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import make_url

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def migration_config(db_url: str) -> Config:
    url = make_url(db_url)
    if url.get_backend_name() == "sqlite" and url.database not in (None, ":memory:"):
        Path(url.database).parent.mkdir(parents=True, exist_ok=True)
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.attributes["db_url"] = db_url
    return config


def upgrade_database(db_url: str) -> None:
    command.upgrade(migration_config(db_url), "head")
