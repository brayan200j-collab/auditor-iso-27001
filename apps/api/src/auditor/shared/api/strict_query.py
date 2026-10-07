"""Allowlist validation for query strings: parameters not declared by the operation are rejected."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from fastapi import Request

from auditor.shared.api.schemas import has_control_characters
from auditor.shared.domain.errors import ValidationFailedError


@lru_cache(maxsize=1024)
def _compile(template: str) -> re.Pattern[str]:
    return re.compile("^" + re.sub(r"\{[^/]+\}", "[^/]+", template) + "$")


def declared_query_parameters(document: dict[str, Any], path: str, method: str) -> set[str] | None:
    """Names of the query parameters of the matching operation, or None if nothing matches."""
    for template, operations in document.get("paths", {}).items():
        operation = operations.get(method.lower())
        if operation is not None and _compile(template).match(path):
            return {
                parameter["name"]
                for parameter in operation.get("parameters", [])
                if parameter.get("in") == "query"
            }
    return None


async def reject_unknown_query_parameters(request: Request) -> None:
    declared = declared_query_parameters(request.app.openapi(), request.url.path, request.method)
    if declared is None:
        return
    unknown = set(request.query_params) - declared
    if unknown:
        raise ValidationFailedError(
            "La solicitud incluye parámetros no permitidos.",
            detail=f"unknown query parameters: {sorted(unknown)}",
        )
    if any(has_control_characters(value) for value in request.query_params.values()):
        raise ValidationFailedError(detail="control characters in query string")
