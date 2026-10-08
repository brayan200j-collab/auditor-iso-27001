from __future__ import annotations

from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.audit.infrastructure.models import AuditLogModel
from auditor.evaluations.domain.consent import CURRENT_CONSENT
from tests.support.factories import create_evaluation
from tests.support.world import World, build_world


@pytest.fixture
async def world(session: AsyncSession) -> World:
    return await build_world(session)


async def _create(client: httpx.AsyncClient, headers: dict[str, str], title: str) -> str:
    response = await client.post("/api/v1/evaluations", json={"title": title}, headers=headers)
    assert response.status_code == 201, response.text
    evaluation_id: str = response.json()["id"]
    return evaluation_id


async def _audit_actions(session: AsyncSession, resource_id: str) -> list[str]:
    rows = await session.scalars(
        select(AuditLogModel.action).where(AuditLogModel.resource_id == resource_id)
    )
    return list(rows.all())


async def test_sme_creates_an_evaluation_for_its_own_company(
    client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    evaluation_id = await _create(client, world.sme_a.headers, "  Autoevaluación 2026 ")
    detail = (
        await client.get(f"/api/v1/evaluations/{evaluation_id}", headers=world.sme_a.headers)
    ).json()
    evaluation = detail["evaluation"]
    assert evaluation["title"] == "Autoevaluación 2026"
    assert evaluation["status"] == "DRAFT"
    assert evaluation["company_id"] == str(world.company_a)
    assert evaluation["company_name"] == "Empresa sintética A"
    assert detail["consent_given"] is False
    assert [step["state"] for step in detail["progress"]] == ["PENDING"] * 5
    assert detail["available_actions"] == ["DOCUMENT_UPLOADED"]
    assert await _audit_actions(session, evaluation_id) == ["EVALUATION_CREATED"]


@pytest.mark.parametrize("member", ["admin", "reviewer", "mentor"])
async def test_only_smes_create_evaluations(
    client: httpx.AsyncClient, world: World, member: str
) -> None:
    headers = getattr(world, member).headers
    response = await client.post("/api/v1/evaluations", json={"title": "Prueba"}, headers=headers)
    assert response.status_code == 403


async def test_evaluation_quota_per_company(
    app: object, client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    app.state.container.settings.max_evaluations_per_company = 2  # type: ignore[attr-defined]
    for number in range(2):
        await _create(client, world.sme_a.headers, f"Evaluación {number}")
    blocked = await client.post(
        "/api/v1/evaluations", json={"title": "Una más"}, headers=world.sme_a.headers
    )
    assert blocked.status_code == 429
    assert blocked.json()["code"] == "QUOTA_EXCEEDED"
    other_company = await client.post(
        "/api/v1/evaluations", json={"title": "Empresa B"}, headers=world.sme_b.headers
    )
    assert other_company.status_code == 201
    quota_events = await session.scalars(
        select(AuditLogModel.action).where(AuditLogModel.action == "QUOTA_EXCEEDED")
    )
    assert len(quota_events.all()) == 1


async def test_listing_is_scoped_by_role(
    client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    eval_a = await create_evaluation(
        session, world.company_a, world.sme_a.id, reviewer_id=world.reviewer.id
    )
    eval_b = await create_evaluation(session, world.company_b, world.sme_b.id)

    async def ids(headers: dict[str, str]) -> set[str]:
        response = await client.get("/api/v1/evaluations", headers=headers)
        assert response.status_code == 200
        return {item["id"] for item in response.json()["items"]}

    assert await ids(world.admin.headers) == {str(eval_a), str(eval_b)}
    assert await ids(world.sme_a.headers) == {str(eval_a)}
    assert await ids(world.sme_b.headers) == {str(eval_b)}
    assert await ids(world.reviewer.headers) == {str(eval_a)}
    assert await ids(world.other_reviewer.headers) == set()
    mentor = await client.get("/api/v1/evaluations", headers=world.mentor.headers)
    assert mentor.status_code == 403


async def test_cross_company_access_is_a_generic_404_and_is_audited(
    client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    eval_b = await create_evaluation(session, world.company_b, world.sme_b.id)
    for path in (f"/api/v1/evaluations/{eval_b}", f"/api/v1/evaluations/{eval_b}/status"):
        response = await client.get(path, headers=world.sme_a.headers)
        assert response.status_code == 404
        assert response.json()["code"] == "NOT_FOUND"
    unknown = await client.get(f"/api/v1/evaluations/{uuid4()}", headers=world.sme_a.headers)
    assert unknown.status_code == 404
    assert unknown.json()["message"] == response.json()["message"]
    denied = await session.scalars(
        select(AuditLogModel).where(AuditLogModel.action == "ACCESS_DENIED")
    )
    entries = denied.all()
    assert len(entries) == 2
    assert {entry.resource_id for entry in entries} == {eval_b}
    assert {entry.actor_id for entry in entries} == {world.sme_a.id}


async def test_consent_is_versioned_and_idempotent(
    client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    evaluation_id = await _create(client, world.sme_a.headers, "Con consentimiento")
    text = (await client.get("/api/v1/consent", headers=world.sme_a.headers)).json()
    assert text["version"] == CURRENT_CONSENT.version
    assert "Ley 1581 de 2012" in text["text"]

    wrong = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/consent",
        json={"version": "2020-01-v0"},
        headers=world.sme_a.headers,
    )
    assert wrong.status_code == 422
    for _ in range(2):
        accepted = await client.post(
            f"/api/v1/evaluations/{evaluation_id}/consent",
            json={"version": text["version"]},
            headers=world.sme_a.headers,
        )
        assert accepted.status_code == 204
    detail = await client.get(f"/api/v1/evaluations/{evaluation_id}", headers=world.sme_a.headers)
    assert detail.json()["consent_given"] is True
    assert (await _audit_actions(session, evaluation_id)).count("CONSENT_GIVEN") == 1

    other_company = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/consent",
        json={"version": text["version"]},
        headers=world.sme_b.headers,
    )
    assert other_company.status_code == 404


async def test_admin_assigns_an_active_reviewer(
    client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    evaluation_id = await create_evaluation(session, world.company_a, world.sme_a.id)
    path = f"/api/v1/evaluations/{evaluation_id}/reviewer"

    not_reviewer = await client.put(
        path, json={"reviewer_id": str(world.mentor.id)}, headers=world.admin.headers
    )
    assert not_reviewer.status_code == 422
    by_sme = await client.put(
        path, json={"reviewer_id": str(world.reviewer.id)}, headers=world.sme_a.headers
    )
    by_reviewer = await client.put(
        path, json={"reviewer_id": str(world.reviewer.id)}, headers=world.reviewer.headers
    )
    assert {by_sme.status_code, by_reviewer.status_code} == {403}

    assigned = await client.put(
        path, json={"reviewer_id": str(world.reviewer.id)}, headers=world.admin.headers
    )
    assert assigned.status_code == 204
    detail = await client.get(
        f"/api/v1/evaluations/{evaluation_id}", headers=world.reviewer.headers
    )
    assert detail.status_code == 200
    assert detail.json()["evaluation"]["reviewer_id"] == str(world.reviewer.id)
    assert "REVIEWER_ASSIGNED" in await _audit_actions(session, str(evaluation_id))
    hidden = await client.get(
        f"/api/v1/evaluations/{evaluation_id}", headers=world.other_reviewer.headers
    )
    assert hidden.status_code == 404


async def test_approved_evaluations_cannot_be_reassigned(
    client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    evaluation_id = await create_evaluation(
        session, world.company_a, world.sme_a.id, status="APPROVED"
    )
    response = await client.put(
        f"/api/v1/evaluations/{evaluation_id}/reviewer",
        json={"reviewer_id": str(world.reviewer.id)},
        headers=world.admin.headers,
    )
    assert response.status_code == 409


async def test_status_endpoint_reports_progress(
    client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    evaluation_id = await create_evaluation(
        session, world.company_a, world.sme_a.id, status="ANALYZING"
    )
    body = (
        await client.get(f"/api/v1/evaluations/{evaluation_id}/status", headers=world.sme_a.headers)
    ).json()
    assert body["status"] == "ANALYZING"
    assert [step["state"] for step in body["progress"]] == [
        "DONE",
        "DONE",
        "CURRENT",
        "PENDING",
        "PENDING",
    ]
