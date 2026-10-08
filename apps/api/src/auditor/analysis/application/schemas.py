"""Structured output expected from the model and its strict JSON Schema.

The model returns chunk identifiers and quotes; document and page are filled in by the system from
the real fragment, and `citation_verified` / `requires_human_review` are always set by the system.
"""

from __future__ import annotations

import copy
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ModelCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: UUID
    quote: str = Field(max_length=400)


class ModelFinding(BaseModel):
    """What the model must return for one criterion."""

    model_config = ConfigDict(extra="forbid")

    criterion_id: str = Field(pattern=r"^ISO-\d{2}$")
    status: Literal["FOUND", "PARTIAL", "NO_DOCUMENTARY_EVIDENCE"]
    confidence: float = Field(ge=0, le=1)
    evidence: list[ModelCitation] = Field(max_length=8)
    gap: str = Field(min_length=1, max_length=1500)
    recommendation: str = Field(min_length=1, max_length=1500)
    preliminary_priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    estimated_effort: Literal["LOW", "MEDIUM", "HIGH"]
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]


SCHEMA_NAME = "auditor_finding"


def _inline(node: Any, definitions: dict[str, Any]) -> Any:
    if isinstance(node, dict):
        if "$ref" in node:
            name = node["$ref"].split("/")[-1]
            return _inline(copy.deepcopy(definitions[name]), definitions)
        return {key: _inline(value, definitions) for key, value in node.items() if key != "title"}
    if isinstance(node, list):
        return [_inline(item, definitions) for item in node]
    return node


def _close_objects(node: Any) -> None:
    if isinstance(node, dict):
        if node.get("type") == "object":
            node["additionalProperties"] = False
            node["required"] = list(node.get("properties", {}))
        for value in node.values():
            _close_objects(value)
    elif isinstance(node, list):
        for item in node:
            _close_objects(item)


def strict_json_schema() -> dict[str, Any]:
    """JSON Schema for strict structured outputs: no $ref, closed objects, all fields required."""
    raw = ModelFinding.model_json_schema()
    definitions = raw.pop("$defs", {})
    schema: dict[str, Any] = _inline(raw, definitions)
    _close_objects(schema)
    return schema
