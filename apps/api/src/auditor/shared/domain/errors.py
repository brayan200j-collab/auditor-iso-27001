"""Domain errors. Each carries a stable machine code and a clear Spanish message for the user.

Internal details go to logs only; they never reach the API response.
"""

from __future__ import annotations


class DomainError(Exception):
    code: str = "DOMAIN_ERROR"
    default_message: str = "No fue posible completar la operación."

    def __init__(self, message: str | None = None, *, detail: str | None = None) -> None:
        self.message = message or self.default_message
        self.detail = detail
        super().__init__(self.message)


class UnauthorizedError(DomainError):
    code = "UNAUTHORIZED"
    default_message = "Debes iniciar sesión para continuar."


class ForbiddenError(DomainError):
    code = "FORBIDDEN"
    default_message = "No tienes permiso para realizar esta acción."


class ResourceNotFoundError(DomainError):
    code = "NOT_FOUND"
    default_message = "El recurso solicitado no existe o no está disponible."


class InvalidFileError(DomainError):
    code = "INVALID_FILE"
    default_message = "El archivo no es válido."


class ProcessingError(DomainError):
    code = "PROCESSING_ERROR"
    default_message = "Ocurrió un problema al procesar la información."


class AIProviderError(DomainError):
    code = "AI_PROVIDER_ERROR"
    default_message = "El servicio de análisis no está disponible en este momento."


class ReportGenerationError(DomainError):
    code = "REPORT_GENERATION_ERROR"
    default_message = "No fue posible generar el informe."


class InvalidStateTransitionError(DomainError):
    code = "INVALID_STATE_TRANSITION"
    default_message = "La acción no está disponible en el estado actual."


class QuotaExceededError(DomainError):
    code = "QUOTA_EXCEEDED"
    default_message = "Se alcanzó el límite de uso permitido para esta operación."


class ConflictError(DomainError):
    code = "CONFLICT"
    default_message = "La operación entra en conflicto con el estado actual del recurso."


class ValidationFailedError(DomainError):
    code = "VALIDATION_ERROR"
    default_message = "Los datos enviados no son válidos."
