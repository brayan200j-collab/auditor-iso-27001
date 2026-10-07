"""Walks the OpenAPI document: every operation except health checks rejects anonymous calls."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI

from tests.support.auth import make_token

PUBLIC_PATHS = {"/healthz", "/readyz"}


def operations(app: FastAPI) -> list[tuple[str, str]]:
    schema: dict[str, Any] = app.openapi()
    return [
        (method.upper(), path)
        for path, methods in schema["paths"].items()
        for method in methods
        if path not in PUBLIC_PATHS
    ]


def concrete(path: str) -> str:
    segments = [str(uuid4()) if part.startswith("{") else part for part in path.split("/")]
    return "/".join(segments)


async def test_every_operation_requires_a_token(app: FastAPI, client: httpx.AsyncClient) -> None:
    found = operations(app)
    assert found, "the API exposes no operations"
    for method, path in found:
        url = concrete(path)
        anonymous = await client.request(method, url)
        forged = await client.request(
            method,
            url,
            headers={"authorization": f"Bearer {make_token(uuid4(), secret='x' * 40)}"},
        )
        assert anonymous.status_code == 401, f"{method} {path} -> {anonymous.status_code}"
        assert forged.status_code == 401, f"{method} {path} (forged) -> {forged.status_code}"


@pytest.mark.parametrize("path", sorted(PUBLIC_PATHS))
async def test_only_health_checks_are_public(client: httpx.AsyncClient, path: str) -> None:
    response = await client.get(path)
    assert response.status_code == 200
