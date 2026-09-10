import argparse
import asyncio
import random
from datetime import UTC, datetime, time, timedelta

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from eufylocal.config import Settings
from eufylocal.db import MeasurementModel
from eufylocal.db.migration import upgrade_database
from eufylocal.schemas.measurement import MeasurementUnit

LOCAL_DATABASE_HOSTS = {"127.0.0.1", "::1", "localhost"}

DAY_HOUR_SLOTS = (8, 13, 20)


def generate_measurements(
    *,
    weeks: int,
    now: datetime,
    seed: int,
) -> list[MeasurementModel]:
    randomizer = random.Random(seed)
    measurements: list[MeasurementModel] = []

    for week_offset in reversed(range(weeks)):
        week_start = now - timedelta(weeks=week_offset + 1)
        days = sorted(randomizer.sample(range(7), randomizer.choice((3, 4))))
        for day in days:
            date = week_start.date() + timedelta(days=day)
            hour_slots = sorted(randomizer.sample(DAY_HOUR_SLOTS, randomizer.choice((2, 3))))
            for hour in hour_slots:
                measured_at = datetime.combine(
                    date,
                    time(hour=hour, minute=randomizer.randint(0, 59), tzinfo=UTC),
                )
                measurements.append(
                    MeasurementModel(
                        measured_at=measured_at,
                        weight=round(76 + randomizer.uniform(-1.2, 1.2), 2),
                        unit=MeasurementUnit.KG,
                        impedance_ohm=round(500 + randomizer.uniform(-25, 25), 1),
                        raw_data=f"cf{int(measured_at.timestamp() * 1_000_000):020x}",
                    )
                )

    return measurements


async def seed_database(db_url: str, measurements: list[MeasurementModel]) -> None:
    engine = create_async_engine(db_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            await session.execute(delete(MeasurementModel))
            session.add_all(measurements)
            await session.commit()
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate local development measurements")
    parser.add_argument("--weeks", type=int, default=1, choices=range(1, 53))
    parser.add_argument("--seed", type=int, default=9146)
    args = parser.parse_args(argv)

    settings = Settings()
    if settings.db_host not in LOCAL_DATABASE_HOSTS:
        parser.error("test data can only be generated for a localhost database")

    measurements = generate_measurements(
        weeks=args.weeks,
        now=datetime.now(UTC),
        seed=args.seed,
    )
    upgrade_database(str(settings.db_url))
    asyncio.run(seed_database(str(settings.db_url), measurements))
    print(f"Generated {len(measurements)} measurements across {args.weeks} week(s)")


if __name__ == "__main__":
    main()
