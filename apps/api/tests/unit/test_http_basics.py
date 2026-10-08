from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import APIRouter, FastAPI

from auditor.container import AppContainer
from auditor.main import create_app
from auditor.shared.domain.errors import (
    InvalidStateTransitionError,
    QuotaExceededError,
    ResourceNotFoundError,
)
from tests.support.settings import make_settings


class _NotReadyContainer(AppContainer):
    async def is_ready(self) -> bool:
        raise ConnectionError("database down")


def _app(ready: bool = True) -> FastAPI:
    settings = make_settings()
    container = AppContainer.build(settings)
    if not ready:
        container.__class__ = _NotReadyContainer
    else:

        async def _ready() -> bool:
            return True

        container.is_ready = _ready  # type: ignore[method-assign]
    app = create_app(settings, container)
    router = APIRouter()

    @router.get("/boom/not-found")
    async def not_found() -> None:
        raise ResourceNotFoundError(detail="internal detail never shown")

    @router.get("/boom/state")
    async def state() -> None:
        raise InvalidStateTransitionError()

    @router.get("/boom/quota")
    async def quota() -> None:
        raise QuotaExceededError("Se alcanzó el número máximo de evaluaciones.")

    @router.get("/boom/unexpected")
    async def unexpected() -> None:
        raise RuntimeError("secret stack detail")

    app.include_router(router)
    return app


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=_app(), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


async def test_healthz(client: httpx.AsyncClient) -> None:
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_readyz_reports_unavailable_when_database_fails() -> None:
    transport = httpx.ASGITransport(app=_app(ready=False))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
        response = await http.get("/readyz")
    assert response.status_code == 503


async def test_request_id_is_generated_and_propagated(client: httpx.AsyncClient) -> None:
    generated = await client.get("/healthz")
    assert len(generated.headers["x-request-id"]) >= 8
    echoed = await client.get("/healthz", headers={"x-request-id": "abc12345-req"})
    assert echoed.headers["x-request-id"] == "abc12345-req"
    rejected = await client.get("/healthz", headers={"x-request-id": "<script>"})
    assert rejected.headers["x-request-id"] != "<script>"


async def test_security_headers(client: httpx.AsyncClient) -> None:
    response = await client.get("/healthz")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


@pytest.mark.parametrize(
    ("path", "status", "code"),
    [
        ("/boom/not-found", 404, "NOT_FOUND"),
        ("/boom/state", 409, "INVALID_STATE_TRANSITION"),
        ("/boom/quota", 429, "QUOTA_EXCEEDED"),
        ("/boom/unexpected", 500, "INTERNAL_ERROR"),
        ("/does-not-exist", 404, "NOT_FOUND"),
    ],
)
async def test_errors_have_uniform_body_without_internal_details(
    client: httpx.AsyncClient, path: str, status: int, code: str
) -> None:
    response = await client.get(path)
    assert response.status_code == status
    body = response.json()
    assert set(body) == {"code", "message", "request_id"}
    assert body["code"] == code
    assert body["request_id"] == response.headers["x-request-id"]
    assert "detail" not in response.text
    assert "secret stack" not in response.text
    assert "Traceback" not in response.text


async def test_cors_only_allows_configured_origins(client: httpx.AsyncClient) -> None:
    allowed = await client.options(
        "/healthz",
        headers={"origin": "http://localhost:3000", "access-control-request-method": "GET"},
    )
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:3000"
    denied = await client.options(
        "/healthz",
        headers={"origin": "https://evil.example", "access-control-request-method": "GET"},
    )
    assert "access-control-allow-origin" not in denied.headers


async def test_method_not_allowed_lists_every_allowed_method() -> None:
    settings = make_settings()
    app = create_app(settings, AppContainer.build(settings))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
        response = await http.request("OPTIONS", "/api/v1/companies")
        malformed = await http.patch(
            "/api/v1/companies/e3e70682-c209-1cac-a29f-6fbed82c07cd",
            content=b"{not json",
            headers={"content-type": "application/json", "authorization": "Bearer x"},
        )
    assert response.status_code == 405
    assert response.headers["allow"] == "GET, POST"
    assert malformed.status_code in {400, 401, 422}


def test_optional_query_parameters_are_not_nullable() -> None:
    document = create_app(make_settings()).openapi()
    parameters = document["paths"]["/api/v1/users"]["get"]["parameters"]
    names = {parameter["name"] for parameter in parameters}
    assert {"role", "company_id", "search", "page", "page_size"} <= names
    role = next(parameter for parameter in parameters if parameter["name"] == "role")
    assert "anyOf" not in role["schema"]
    assert role["schema"]["$ref"].endswith("/Role")


async def test_undeclared_query_parameters_are_rejected() -> None:
    settings = make_settings()
    app = create_app(settings, AppContainer.build(settings))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
        extra = await http.get("/healthz", params={"debug": "1"})
        empty_name = await http.get("/api/v1/companies?page=1&=x")
    assert extra.status_code == 422
    assert extra.json()["code"] == "VALIDATION_ERROR"
    assert empty_name.status_code == 422
