from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ErrorResponse(ApiModel):
    code: str
    message: str
    request_id: str | None


class PageMeta(ApiModel):
    total: int
    page: int
    page_size: int


ERROR_RESPONSES: dict[int | str, dict[str, object]] = {
    401: {"model": ErrorResponse, "description": "No autenticado"},
    403: {"model": ErrorResponse, "description": "Sin permiso"},
    404: {"model": ErrorResponse, "description": "No encontrado"},
    422: {"model": ErrorResponse, "description": "Datos no válidos"},
}
