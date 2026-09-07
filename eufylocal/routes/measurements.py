from typing import cast

from fastapi import APIRouter, Query, Request

from eufylocal.db import MeasurementRepository
from eufylocal.schemas import MeasurementResponse, MeasurementsResponse

router = APIRouter(prefix="/api/measurements", tags=["measurements"])


def _repository(request: Request) -> MeasurementRepository:
    return cast(MeasurementRepository, request.app.state.measurements)


@router.get("", response_model=MeasurementsResponse)
def measurements(
    request: Request,
    limit: int = Query(default=50, ge=1, le=500),
) -> MeasurementsResponse:
    items = _repository(request).list(limit=limit)
    return MeasurementsResponse(
        measurements=[MeasurementResponse.model_validate(item) for item in items]
    )


@router.get("/latest", response_model=MeasurementResponse | None)
def latest_measurement(request: Request) -> MeasurementResponse | None:
    latest = _repository(request).latest()
    return MeasurementResponse.model_validate(latest) if latest else None
