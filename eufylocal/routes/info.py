from typing import cast

from fastapi import APIRouter, Request

from eufylocal.schemas import StatusResponse
from eufylocal.state import AppState

router = APIRouter(prefix="/api", tags=["info"])


@router.get("/status", response_model=StatusResponse)
def status(request: Request) -> StatusResponse:
    state = cast(AppState, request.app.state.runtime)
    return StatusResponse.model_validate(state.snapshot())
