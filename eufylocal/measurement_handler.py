from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from eufylocal.db import Database, MeasurementModel, MeasurementRepository
from eufylocal.parser import parse_frame
from eufylocal.state import AppState

logger = logging.getLogger(__name__)


class MeasurementHandler:
    def __init__(
        self,
        database: Database,
        state: AppState,
        latest_measurement: MeasurementModel | None = None,
    ) -> None:
        self._database = database
        self._state = state
        self._last_persisted_key = (
            self._dedup_key(latest_measurement) if latest_measurement is not None else None
        )
        self._persist_lock = asyncio.Lock()

    async def handle_frame(
        self,
        *,
        frame: bytes,
        source: str,
        device_id: str,
        received_at: datetime,
    ) -> None:
        parsed = parse_frame(frame)
        if parsed is None:
            logger.warning("unparseable frame ignored: %s", frame.hex())
            return

        self._state.set_last_received_at(received_at)

        logger.info(
            "parsed frame: weight=%.2f kg impedance=%s final=%s unit=%s source=%s",
            parsed.weight_kg,
            parsed.impedance_ohm,
            parsed.is_final,
            parsed.unit,
            source,
        )

        self._state.set_live_weight(parsed.weight_kg, active=not parsed.is_final)

        if parsed.weight_limit_exceeded:
            logger.warning("weight limit exceeded (max weight on scale)")
            return

        if not parsed.is_final:
            logger.debug("ignoring non-final (unstable) frame")
            return

        measurement = MeasurementModel.from_received(
            received_at=received_at,
            weight_kg=parsed.weight_kg,
            impedance_ohm=parsed.impedance_ohm,
            device_id=device_id,
            source=source,
            raw_payload_hex=frame.hex(),
        )

        async with self._persist_lock:
            if self._is_duplicate(measurement):
                logger.debug("duplicate final measurement skipped")
                return

            async with self._database.session() as session:
                await MeasurementRepository(session).insert(measurement)
            self._state.set_last_measurement(measurement)
            self._last_persisted_key = self._dedup_key(measurement)
        logger.info(
            "stored measurement: weight=%.2f kg impedance=%s source=%s",
            measurement.weight_kg,
            measurement.impedance_ohm,
            source,
        )

    def _is_duplicate(self, measurement: MeasurementModel) -> bool:
        return self._dedup_key(measurement) == self._last_persisted_key

    @staticmethod
    def _dedup_key(measurement: MeasurementModel) -> tuple[str, str]:
        return measurement.device_id, measurement.raw_payload_hex
