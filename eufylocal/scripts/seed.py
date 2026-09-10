from __future__ import annotations

import argparse
import asyncio
import random
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from eufylocal.config import Settings
from eufylocal.db import MeasurementModel
from eufylocal.db.migration import upgrade_database

DEV_DEVICE_ID = "DEV-SCALE"
LOCAL_DATABASE_HOSTS = {"127.0.0.1", "::1", "localhost"}


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
            measured_at = week_start + timedelta(
                days=day,
                hours=randomizer.randint(7, 9),
                minutes=randomizer.randint(0, 59),
            )
            measurements.append(
                MeasurementModel(
                    measured_at=measured_at,
                    weight=round(80 + randomizer.uniform(-1.2, 1.2), 2),
                    impedance_ohm=round(500 + randomizer.uniform(-25, 25), 1),
                    device_id=DEV_DEVICE_ID,
                    raw_payload_hex=f"cf{int(measured_at.timestamp() * 1_000_000):020x}",
                )
            )

    return measurements


async def seed_database(db_url: str, measurements: list[MeasurementModel]) -> None:
    engine = create_async_engine(db_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            await session.execute(
                delete(MeasurementModel).where(MeasurementModel.device_id == DEV_DEVICE_ID)
            )
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
