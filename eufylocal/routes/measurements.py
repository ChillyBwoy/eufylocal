from fastapi import APIRouter, Query, Response, status

from eufylocal.db.exceptions import DbEntityNotFoundError
from eufylocal.di import MeasurementRepositoryDep
from eufylocal.exceptions import HTTPError
from eufylocal.schemas.measurement import Measurement, MeasurementUpdate

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


@router.patch("/{measurement_id}", response_model=Measurement, operation_id="update_measurement")
async def update_measurement(
    measurement_id: int,
    payload: MeasurementUpdate,
    repository: MeasurementRepositoryDep,
) -> Measurement:
    try:
        measurement = await repository.update_user(measurement_id, payload.user_id)
        return Measurement.model_validate(measurement)
    except DbEntityNotFoundError as error:
        raise HTTPError(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found") from error


@router.delete(
    "/{measurement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_measurement",
)
async def delete_measurement(
    measurement_id: int,
    repository: MeasurementRepositoryDep,
) -> Response:
    if not await repository.delete(measurement_id):
        raise HTTPError(status_code=status.HTTP_404_NOT_FOUND, detail="Measurement not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
