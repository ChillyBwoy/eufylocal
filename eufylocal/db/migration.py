from pathlib import Path

from alembic import command
from alembic.config import Config

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def migration_config(db_url: str) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.attributes["db_url"] = db_url
    return config


def upgrade_database(db_url: str) -> None:
    command.upgrade(migration_config(db_url), "head")
