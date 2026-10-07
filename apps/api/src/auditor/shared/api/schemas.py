from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

# C0 control characters except tab, line feed and carriage return (NUL breaks PostgreSQL text).
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def has_control_characters(value: str) -> bool:
    return bool(_CONTROL_CHARACTERS.search(value))


def _contains_control_characters(value: Any) -> bool:
    if isinstance(value, str):
        return has_control_characters(value)
    if isinstance(value, dict):
        return any(_contains_control_characters(item) for item in value.values())
    if isinstance(value, list | tuple):
        return any(_contains_control_characters(item) for item in value)
    return False


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RequestModel(ApiModel):
    """Base for request bodies: rejects control characters in any string field."""

    @model_validator(mode="before")
    @classmethod
    def _reject_control_characters(cls, data: Any) -> Any:
        if _contains_control_characters(data):
            raise ValueError("text contains control characters")
        return data


class ErrorResponse(ApiModel):
    code: str
    message: str
    request_id: str | None


class PageMeta(ApiModel):
    total: int
    page: int
    page_size: int


ERROR_RESPONSES: dict[int | str, dict[str, object]] = {
    400: {"model": ErrorResponse, "description": "Solicitud con formato no válido"},
    401: {"model": ErrorResponse, "description": "No autenticado"},
    403: {"model": ErrorResponse, "description": "Sin permiso"},
    404: {"model": ErrorResponse, "description": "No encontrado"},
    409: {"model": ErrorResponse, "description": "Conflicto con el estado actual"},
    422: {"model": ErrorResponse, "description": "Datos no válidos"},
    429: {"model": ErrorResponse, "description": "Límite de uso alcanzado"},
}
