from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from datetime import datetime

from eufylocal.parser import parse_frame
from eufylocal.schemas import (
    FinalMeasurementReceived,
    MeasurementSource,
    StatusEvent,
)

logger = logging.getLogger(__name__)


class MeasurementHandler:
    def __init__(
        self,
        on_status_event: Callable[..., None],
        on_final_measurement: Callable[[FinalMeasurementReceived], Awaitable[None]],
    ) -> None:
        self._on_status_event = on_status_event
        self._on_final_measurement = on_final_measurement

    async def handle_frame(
        self,
        *,
        frame: bytes,
        source: MeasurementSource,
        device_id: str,
        received_at: datetime,
    ) -> None:
        parsed = parse_frame(frame)
        if parsed is None:
            logger.warning("unparseable frame ignored: %s", frame.hex())
            return

        self._on_status_event(
            StatusEvent.READING_RECEIVED,
            received_at=received_at,
            weight_kg=parsed.weight_kg,
            is_final=parsed.is_final,
        )
        logger.info(
            "parsed frame: weight=%.2f kg impedance=%s final=%s unit=%s source=%s",
            parsed.weight_kg,
            parsed.impedance_ohm,
            parsed.is_final,
            parsed.unit,
            source,
        )

        if parsed.weight_limit_exceeded:
            logger.warning("weight limit exceeded (max weight on scale)")
            return
        if not parsed.is_final:
            logger.debug("ignoring non-final (unstable) frame")
            return

        await self._on_final_measurement(
            FinalMeasurementReceived(
                measured_at=received_at,
                weight_kg=parsed.weight_kg,
                impedance_ohm=parsed.impedance_ohm,
                device_id=device_id,
                source=source,
                raw_payload_hex=frame.hex(),
            )
        )
