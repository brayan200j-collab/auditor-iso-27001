from __future__ import annotations

from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.audit.infrastructure.models import AuditLogModel
from auditor.shared.domain.actor import Role
from tests.support.auth import auth_headers, make_token
from tests.support.factories import create_company, create_user


async def test_me_requires_a_token(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/me")
    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


async def test_me_rejects_invalid_and_unknown_users(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    invalid = await client.get("/api/v1/me", headers={"authorization": "Bearer nope"})
    unknown = await client.get("/api/v1/me", headers=auth_headers(uuid4()))
    inactive_user = await create_user(session, Role.REVIEWER, active=False)
    inactive = await client.get("/api/v1/me", headers=auth_headers(inactive_user.id))
    expired = await client.get(
        "/api/v1/me",
        headers={"authorization": f"Bearer {make_token(inactive_user.id, expires_in=-30)}"},
    )
    assert {r.status_code for r in (invalid, unknown, inactive, expired)} == {401}


async def test_me_returns_profile_with_company_from_database(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    company_id = await create_company(session, "Empresa sintética Uno")
    user = await create_user(session, Role.SME, company_id)
    # Claims cannot elevate privileges: role and company come from the database.
    token = make_token(user.id, app_metadata={"role": "ADMIN"}, company_id=str(uuid4()))
    response = await client.get("/api/v1/me", headers={"authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "SME"
    assert body["company_id"] == str(company_id)
    assert body["company_name"] == "Empresa sintética Uno"


async def test_login_and_logout_events_are_audited(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    user = await create_user(session, Role.REVIEWER)
    for path in ("/api/v1/auth/login-event", "/api/v1/auth/logout-event"):
        response = await client.post(path, headers=auth_headers(user.id))
        assert response.status_code == 204
    actions = (
        await session.scalars(select(AuditLogModel.action).where(AuditLogModel.actor_id == user.id))
    ).all()
    assert sorted(actions) == ["LOGIN", "LOGOUT"]


async def test_audit_logs_are_admin_only(client: httpx.AsyncClient, session: AsyncSession) -> None:
    admin = await create_user(session, Role.ADMIN)
    reviewer = await create_user(session, Role.REVIEWER)
    await client.post("/api/v1/auth/login-event", headers=auth_headers(reviewer.id))

    denied = await client.get("/api/v1/audit-logs", headers=auth_headers(reviewer.id))
    allowed = await client.get(
        "/api/v1/audit-logs",
        params={"action": "LOGIN", "page": 1, "page_size": 10},
        headers=auth_headers(admin.id),
    )

    assert denied.status_code == 403
    assert allowed.status_code == 200
    body = allowed.json()
    assert body["meta"]["total"] == 1
    assert body["items"][0]["actor_id"] == str(reviewer.id)
    assert body["items"][0]["request_id"]
