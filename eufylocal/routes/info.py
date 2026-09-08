from typing import cast

from fastapi import APIRouter, Request

from eufylocal.schemas import Status
from eufylocal.state import AppState

router = APIRouter(prefix="/api", tags=["info"])


@router.get(
    "/status",
    response_model=Status,
    operation_id="get_status",
)
def status(request: Request) -> Status:
    state = cast(AppState, request.app.state.runtime)
    return Status.model_validate(state.snapshot())
