from pathlib import Path

from alembic import command
from alembic.config import Config

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def migration_config(database_path: Path) -> Config:
    if database_path != Path(":memory:"):
        database_path.parent.mkdir(parents=True, exist_ok=True)
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.attributes["database_path"] = database_path
    return config


def upgrade_database(database_path: Path) -> None:
    command.upgrade(migration_config(database_path), "head")
