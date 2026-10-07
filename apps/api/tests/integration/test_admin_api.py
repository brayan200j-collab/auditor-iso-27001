from __future__ import annotations

from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.audit.infrastructure.models import AuditLogModel
from auditor.shared.domain.actor import Role
from tests.support.auth import auth_headers
from tests.support.factories import create_company, create_user
from tests.support.fakes import FakeAuthAdmin


@pytest.fixture
async def admin_headers(session: AsyncSession) -> dict[str, str]:
    admin = await create_user(session, Role.ADMIN)
    return auth_headers(admin.id)


async def _actions(session: AsyncSession) -> list[str]:
    return list((await session.scalars(select(AuditLogModel.action))).all())


# ----------------------------------------------------------------------------- companies


async def test_admin_manages_companies(
    client: httpx.AsyncClient, session: AsyncSession, admin_headers: dict[str, str]
) -> None:
    created = await client.post(
        "/api/v1/companies",
        json={"name": "  Ferretería  Sintética ", "tax_id": "900123456-7", "city": "Cali"},
        headers=admin_headers,
    )
    assert created.status_code == 201
    company = created.json()
    assert company["name"] == "Ferretería Sintética"
    assert company["tax_id"] == "900123456-7"

    updated = await client.patch(
        f"/api/v1/companies/{company['id']}",
        json={"name": "Ferretería Sintética S.A.S.", "tax_id": "900123456-7", "active": False},
        headers=admin_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["active"] is False

    listed = await client.get(
        "/api/v1/companies", params={"search": "ferre", "page_size": 5}, headers=admin_headers
    )
    assert listed.json()["meta"]["total"] == 1
    assert await _actions(session) == ["COMPANY_CREATED", "COMPANY_UPDATED"]


async def test_company_validation_and_conflicts(
    client: httpx.AsyncClient, admin_headers: dict[str, str]
) -> None:
    payload = {"name": "Empresa sintética", "tax_id": "800111222-3"}
    assert (
        await client.post("/api/v1/companies", json=payload, headers=admin_headers)
    ).status_code == 201
    duplicate = await client.post("/api/v1/companies", json=payload, headers=admin_headers)
    assert duplicate.status_code == 409
    assert duplicate.json()["message"] == "Ya existe una empresa con ese NIT."
    for tax_id in ("ABC-123", "900.123.456-7", "0" * 39):
        invalid = await client.post(
            "/api/v1/companies", json={"name": "Otra", "tax_id": tax_id}, headers=admin_headers
        )
        assert invalid.status_code == 422
    missing = await client.get(f"/api/v1/companies/{uuid4()}", headers=admin_headers)
    assert missing.status_code == 404


@pytest.mark.parametrize("role", [Role.SME, Role.REVIEWER, Role.MENTOR])
async def test_only_admins_manage_companies_and_users(
    client: httpx.AsyncClient, session: AsyncSession, role: Role
) -> None:
    company_id = await create_company(session)
    user = await create_user(session, role, company_id if role is Role.SME else None)
    headers = auth_headers(user.id)
    responses = [
        await client.get("/api/v1/companies", headers=headers),
        await client.post("/api/v1/companies", json={"name": "Nueva"}, headers=headers),
        await client.get("/api/v1/users", headers=headers),
        await client.patch(f"/api/v1/users/{user.id}", json={"active": True}, headers=headers),
    ]
    assert {response.status_code for response in responses} == {403}


# ----------------------------------------------------------------------------- users


async def test_admin_invites_an_sme_user(
    client: httpx.AsyncClient,
    session: AsyncSession,
    admin_headers: dict[str, str],
    auth_admin: FakeAuthAdmin,
) -> None:
    company_id = await create_company(session)
    response = await client.post(
        "/api/v1/users",
        json={
            "email": "Gerencia@Example.test",
            "full_name": "Gerencia Sintética",
            "role": "SME",
            "company_id": str(company_id),
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "gerencia@example.test"
    assert body["company_id"] == str(company_id)
    assert auth_admin.invited == ["gerencia@example.test"]
    assert "USER_CREATED" in await _actions(session)

    duplicate = await client.post(
        "/api/v1/users",
        json={
            "email": "gerencia@example.test",
            "full_name": "Otra persona",
            "role": "SME",
            "company_id": str(company_id),
        },
        headers=admin_headers,
    )
    assert duplicate.status_code == 409


@pytest.mark.parametrize(
    ("role", "with_company", "message"),
    [
        ("SME", False, "Un usuario PYME debe pertenecer a una empresa."),
        ("REVIEWER", True, "Solo los usuarios PYME se asocian a una empresa."),
    ],
)
async def test_role_and_company_must_be_consistent(
    client: httpx.AsyncClient,
    session: AsyncSession,
    admin_headers: dict[str, str],
    role: str,
    with_company: bool,
    message: str,
) -> None:
    company_id = await create_company(session) if with_company else None
    response = await client.post(
        "/api/v1/users",
        json={
            "email": f"{role.lower()}@example.test",
            "full_name": "Persona sintética",
            "role": role,
            "company_id": str(company_id) if company_id else None,
        },
        headers=admin_headers,
    )
    assert response.status_code == 422
    assert response.json()["message"] == message


async def test_unknown_company_is_rejected(
    client: httpx.AsyncClient, admin_headers: dict[str, str], auth_admin: FakeAuthAdmin
) -> None:
    response = await client.post(
        "/api/v1/users",
        json={
            "email": "x@example.test",
            "full_name": "Persona sintética",
            "role": "SME",
            "company_id": str(uuid4()),
        },
        headers=admin_headers,
    )
    assert response.status_code == 422
    assert auth_admin.invited == []


async def test_deactivation_blocks_the_account_and_admins_cannot_lock_themselves_out(
    client: httpx.AsyncClient, session: AsyncSession, auth_admin: FakeAuthAdmin
) -> None:
    admin = await create_user(session, Role.ADMIN)
    reviewer = await create_user(session, Role.REVIEWER)
    headers = auth_headers(admin.id)

    deactivated = await client.patch(
        f"/api/v1/users/{reviewer.id}", json={"active": False}, headers=headers
    )
    assert deactivated.json()["active"] is False
    assert reviewer.id in auth_admin.banned
    me = await client.get("/api/v1/me", headers=auth_headers(reviewer.id))
    assert me.status_code == 401

    await client.patch(f"/api/v1/users/{reviewer.id}", json={"active": True}, headers=headers)
    assert reviewer.id not in auth_admin.banned

    self_lockout = await client.patch(
        f"/api/v1/users/{admin.id}", json={"active": False}, headers=headers
    )
    assert self_lockout.status_code == 409


async def test_users_can_be_filtered_by_role(
    client: httpx.AsyncClient, session: AsyncSession, admin_headers: dict[str, str]
) -> None:
    await create_user(session, Role.REVIEWER)
    await create_user(session, Role.MENTOR)
    response = await client.get(
        "/api/v1/users", params={"role": "REVIEWER", "page": 1}, headers=admin_headers
    )
    assert [user["role"] for user in response.json()["items"]] == ["REVIEWER"]


async def test_control_characters_and_like_wildcards_are_handled_safely(
    client: httpx.AsyncClient, session: AsyncSession, admin_headers: dict[str, str]
) -> None:
    await create_company(session, "Empresa_100% sintética")
    await create_company(session, "Empresa normal")

    wildcard = await client.get(
        "/api/v1/companies", params={"search": "_100%"}, headers=admin_headers
    )
    assert [item["name"] for item in wildcard.json()["items"]] == ["Empresa_100% sintética"]
    everything = await client.get(
        "/api/v1/companies", params={"search": "%"}, headers=admin_headers
    )
    assert everything.json()["meta"]["total"] == 1

    nul_query = await client.get(
        "/api/v1/users", params={"search": "a\x00b"}, headers=admin_headers
    )
    nul_body = await client.post(
        "/api/v1/companies", json={"name": "Mala\x00empresa"}, headers=admin_headers
    )
    assert nul_query.status_code == 422
    assert nul_body.status_code == 422
