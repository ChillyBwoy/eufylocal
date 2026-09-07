from fastapi import APIRouter, Query

from eufylocal.di import MeasurementRepositoryDep
from eufylocal.schemas import MeasurementResponse, MeasurementsResponse

router = APIRouter(prefix="/api/measurements", tags=["measurements"])


@router.get("", response_model=MeasurementsResponse)
async def measurements(
    repository: MeasurementRepositoryDep,
    limit: int = Query(default=50, ge=1, le=500),
) -> MeasurementsResponse:
    items = await repository.list(limit=limit)
    return MeasurementsResponse(
        measurements=[MeasurementResponse.model_validate(item) for item in items]
    )


@router.get("/latest", response_model=MeasurementResponse | None)
async def latest_measurement(repository: MeasurementRepositoryDep) -> MeasurementResponse | None:
    latest = await repository.latest()
    return MeasurementResponse.model_validate(latest) if latest else None
