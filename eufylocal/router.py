from fastapi import APIRouter

from eufylocal.exceptions import api_http_error_responses
from eufylocal.routes import measurements, sse, users

api_router = APIRouter(
    responses=api_http_error_responses,
)

API_PREFIX = "/api"

api_router.include_router(sse.router, prefix=API_PREFIX)
api_router.include_router(measurements.router, prefix=API_PREFIX)
api_router.include_router(users.router, prefix=API_PREFIX)
