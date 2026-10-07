"""Global error handlers: uniform `{code, message, request_id}` bodies, never stack traces.

Unexpected exceptions are turned into a 500 body by `RequestIdMiddleware`.
"""

from __future__ import annotations

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from auditor.shared.api.middleware import current_request_id
from auditor.shared.api.schemas import ErrorResponse
from auditor.shared.domain.errors import (
    AIProviderError,
    ConflictError,
    DomainError,
    ForbiddenError,
    InvalidFileError,
    InvalidStateTransitionError,
    ProcessingError,
    QuotaExceededError,
    ReportGenerationError,
    ResourceNotFoundError,
    UnauthorizedError,
    ValidationFailedError,
)

logger = structlog.get_logger(__name__)

_SERVER_ERROR = 500

_STATUS_BY_ERROR: dict[type[DomainError], int] = {
    UnauthorizedError: 401,
    ForbiddenError: 403,
    ResourceNotFoundError: 404,
    ConflictError: 409,
    InvalidStateTransitionError: 409,
    InvalidFileError: 422,
    ValidationFailedError: 422,
    QuotaExceededError: 429,
    AIProviderError: 503,
    ProcessingError: 500,
    ReportGenerationError: 500,
}

_HTTP_MESSAGES: dict[int, tuple[str, str]] = {
    401: ("UNAUTHORIZED", "Debes iniciar sesión para continuar."),
    403: ("FORBIDDEN", "No tienes permiso para realizar esta acción."),
    404: ("NOT_FOUND", "El recurso solicitado no existe o no está disponible."),
    405: ("METHOD_NOT_ALLOWED", "Operación no permitida."),
    413: ("PAYLOAD_TOO_LARGE", "El archivo supera el tamaño máximo permitido."),
    415: ("UNSUPPORTED_MEDIA_TYPE", "Tipo de contenido no admitido."),
    429: ("RATE_LIMITED", "Demasiadas solicitudes. Intenta de nuevo en unos minutos."),
}


def error_body(code: str, message: str) -> dict[str, str | None]:
    return ErrorResponse(code=code, message=message, request_id=current_request_id()).model_dump()


def status_for(error: DomainError) -> int:
    for error_type in type(error).__mro__:
        if error_type in _STATUS_BY_ERROR:
            return _STATUS_BY_ERROR[error_type]
    return 400


async def _handle_domain_error(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, DomainError):
        raise exc
    status = status_for(exc)
    log = logger.warning if status < _SERVER_ERROR else logger.error
    log("domain_error", code=exc.code, status=status, detail=exc.detail)
    return JSONResponse(status_code=status, content=error_body(exc.code, exc.message))


async def _handle_validation_error(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc
    fields = sorted({".".join(str(part) for part in err.get("loc", ())) for err in exc.errors()})
    logger.info("request_validation_failed", fields=fields)
    return JSONResponse(
        status_code=422,
        content=error_body("VALIDATION_ERROR", "Los datos enviados no son válidos."),
    )


async def _handle_http_error(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        raise exc
    code, message = _HTTP_MESSAGES.get(
        exc.status_code, ("HTTP_ERROR", "No fue posible completar la solicitud.")
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(code, message),
        headers=getattr(exc, "headers", None),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _handle_domain_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_error)
