"""OpenAPI adjustments so the published contract matches what the API actually accepts."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def _drop_null_variant(schema: dict[str, Any]) -> dict[str, Any]:
    variants = schema.get("anyOf")
    if not isinstance(variants, list):
        return schema
    remaining = [variant for variant in variants if variant.get("type") != "null"]
    if len(remaining) == len(variants):
        return schema
    cleaned = {key: value for key, value in schema.items() if key != "anyOf"}
    if len(remaining) == 1:
        return {**cleaned, **remaining[0]}
    return {**cleaned, "anyOf": remaining}


def _fix_query_parameters(document: dict[str, Any]) -> None:
    """A query string cannot carry null: optional query parameters are simply omitted."""
    for operations in document.get("paths", {}).values():
        for operation in operations.values():
            for parameter in operation.get("parameters", []):
                if parameter.get("in") == "query" and "schema" in parameter:
                    parameter["schema"] = _drop_null_variant(parameter["schema"])


def install_openapi(app: FastAPI) -> None:
    def build() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        document = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        _fix_query_parameters(document)
        app.openapi_schema = document
        return document

    app.openapi = build  # type: ignore[method-assign]
