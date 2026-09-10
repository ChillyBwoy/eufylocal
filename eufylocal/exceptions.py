from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException


@dataclass
class HTTPErrorModel:
    description: str | None


class HTTPError(HTTPException, HTTPErrorModel): ...


api_http_error_responses: dict[int | str, dict[str, Any]] = {
    401: {"model": HTTPError},
    403: {"model": HTTPError},
    404: {"model": HTTPError},
}
