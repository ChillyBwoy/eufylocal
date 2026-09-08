from datetime import UTC, datetime

from fastapi import APIRouter

from eufylocal.di import AppStateDep, MeasurementRepositoryDep
from eufylocal.schemas import Measurement, Status

router = APIRouter(prefix="/api", tags=["info"])


@router.get(
    "/status",
    response_model=Status,
    operation_id="get_status",
)
async def status(
    state: AppStateDep,
    repository: MeasurementRepositoryDep,
) -> Status:
    latest = await repository.latest()
    bluetooth = state.current()
    if latest is not None and (
        bluetooth.last_received_at is None or latest.measured_at > bluetooth.last_received_at
    ):
        bluetooth = bluetooth.model_copy(update={"last_received_at": latest.measured_at})
    return Status(
        bluetooth=bluetooth,
        last_measurement=(Measurement.model_validate(latest) if latest is not None else None),
        server_time=datetime.now(UTC),
    )
