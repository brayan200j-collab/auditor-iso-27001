from __future__ import annotations

from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.main import create_app
from tests.support.factories import seed_checklist
from tests.support.settings import make_settings
from tests.support.world import World, build_world


@pytest.fixture
async def world(session: AsyncSession) -> World:
    await seed_checklist(session)
    return await build_world(session)


@pytest.fixture
async def limited(database_url: str, tmp_path: object) -> httpx.AsyncClient:
    app: FastAPI = create_app(
        make_settings(
            database_url=database_url,
            rate_limit_default="5/minute",
            rate_limit_start="2/minute",
            rate_limit_download="2/minute",
        )
    )
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


async def test_sensitive_operations_are_limited_per_session(
    limited: httpx.AsyncClient, world: World
) -> None:
    url = f"/api/v1/reports/{uuid4()}/download"
    statuses = [(await limited.get(url, headers=world.sme_a.headers)).status_code for _ in range(3)]
    assert statuses == [404, 404, 429]
    blocked = await limited.get(url, headers=world.sme_a.headers)
    body = blocked.json()
    assert body["code"] == "RATE_LIMITED"
    assert "Demasiadas solicitudes" in body["message"]
    assert int(blocked.headers["retry-after"]) >= 1
    # Another session keeps its own budget.
    assert (await limited.get(url, headers=world.sme_b.headers)).status_code == 404


async def test_every_api_route_has_a_general_limit(
    limited: httpx.AsyncClient, world: World
) -> None:
    statuses = [
        (await limited.get("/api/v1/me", headers=world.admin.headers)).status_code for _ in range(6)
    ]
    assert statuses[:5] == [200] * 5
    assert statuses[5] == 429
    assert (await limited.get("/healthz")).status_code == 200
