from __future__ import annotations

import asyncio
import logging

from eufylocal.db import MeasurementModel, MeasurementRepository
from eufylocal.schemas import FinalMeasurementReceived

logger = logging.getLogger(__name__)


class MeasurementWriter:
    def __init__(self, repository: MeasurementRepository) -> None:
        self._repository = repository
        self._lock = asyncio.Lock()

    async def __call__(self, event: FinalMeasurementReceived) -> None:
        measurement = MeasurementModel(
            measured_at=event.measured_at,
            weight_kg=round(event.weight_kg, 2),
            impedance_ohm=(
                round(event.impedance_ohm, 1) if event.impedance_ohm is not None else None
            ),
            device_id=event.device_id,
            source=event.source,
            raw_payload_hex=event.raw_payload_hex,
        )

        async with self._lock:
            try:
                key = self._dedup_key(measurement)
                latest = await self._repository.latest()
                if latest is not None and key == self._dedup_key(latest):
                    logger.debug("duplicate final measurement skipped")
                    return
                await self._repository.insert(measurement)
            except Exception:
                await self._repository.session.rollback()
                raise
            finally:
                if self._repository.session.in_transaction():
                    await self._repository.session.rollback()

        logger.info(
            "stored measurement: weight=%.2f kg impedance=%s source=%s",
            measurement.weight_kg,
            measurement.impedance_ohm,
            measurement.source,
        )

    @staticmethod
    def _dedup_key(measurement: MeasurementModel) -> tuple[str, str]:
        return measurement.device_id, measurement.raw_payload_hex
