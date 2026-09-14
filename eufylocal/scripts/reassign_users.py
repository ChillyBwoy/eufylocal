import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from eufylocal.config import Settings
from eufylocal.db.migration import upgrade_database
from eufylocal.db.repositories import MeasurementRepository
from eufylocal.scripts.seed import LOCAL_DATABASE_HOSTS


async def reassign_users(db_url: str) -> tuple[int, int]:
    engine = create_async_engine(db_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            repository = MeasurementRepository(session)
            return await repository.reassign_users_by_weight()
    finally:
        await engine.dispose()


def main() -> None:
    settings = Settings()
    if settings.db_host not in LOCAL_DATABASE_HOSTS:
        raise SystemExit("measurement users can only be reassigned in a localhost database")

    db_url = str(settings.db_url)
    upgrade_database(db_url)
    user_count, measurement_count = asyncio.run(reassign_users(db_url))
    print(f"Reassigned {measurement_count} measurement(s) from {user_count} user reference(s)")


if __name__ == "__main__":
    main()
