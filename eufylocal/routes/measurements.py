from fastapi import APIRouter, Query

from eufylocal.di import MeasurementRepositoryDep
from eufylocal.schemas.measurement import Measurement

router = APIRouter(tags=["measurements"], prefix="/measurements")


@router.get("/", response_model=list[Measurement], operation_id="get_measurements")
async def measurements(
    repository: MeasurementRepositoryDep,
    limit: int = Query(default=50, ge=1, le=500),
) -> list[Measurement]:
    items = await repository.list(limit=limit)
    return [Measurement.model_validate(item) for item in items]


@router.get("/latest", response_model=Measurement | None, operation_id="get_latest_measurement")
async def latest_measurement(
    repository: MeasurementRepositoryDep,
) -> Measurement | None:
    latest = await repository.latest()
    return Measurement.model_validate(latest) if latest else None
