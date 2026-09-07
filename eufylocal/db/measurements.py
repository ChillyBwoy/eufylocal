from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from eufylocal.db.connection import Database
from eufylocal.models import Measurement


class MeasurementRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def insert(self, measurement: Measurement) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO measurements
                    (measured_at, weight_kg, impedance_ohm, device_id, source, raw_payload_hex)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    measurement.measured_at.astimezone(UTC).isoformat(),
                    measurement.weight_kg,
                    measurement.impedance_ohm,
                    measurement.device_id,
                    measurement.source,
                    measurement.raw_payload_hex,
                ),
            )

    def list(self, limit: int = 50) -> list[Measurement]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM measurements ORDER BY measured_at DESC, id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_measurement(row) for row in rows]

    def latest(self) -> Measurement | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM measurements ORDER BY measured_at DESC, id DESC LIMIT 1"
            ).fetchone()
        return self._row_to_measurement(row) if row else None

    @staticmethod
    def _row_to_measurement(row: sqlite3.Row) -> Measurement:
        measured_at = datetime.fromisoformat(row["measured_at"]).astimezone(UTC)
        return Measurement(
            measured_at=measured_at,
            weight_kg=row["weight_kg"],
            impedance_ohm=row["impedance_ohm"],
            device_id=row["device_id"],
            source=row["source"],
            raw_payload_hex=row["raw_payload_hex"],
        )
