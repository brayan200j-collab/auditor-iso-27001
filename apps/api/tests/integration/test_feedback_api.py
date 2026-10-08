from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.audit.infrastructure.models import AuditLogModel
from auditor.feedback.infrastructure.models import FeedbackModel
from tests.integration.test_reports_api import _approve
from tests.support import pdfs
from tests.support.factories import seed_checklist
from tests.support.pipeline import extracted_run
from tests.support.world import World, build_world


@pytest.fixture
async def world(session: AsyncSession) -> World:
    await seed_checklist(session)
    return await build_world(session)


@pytest.fixture
async def analysed(
    app: FastAPI, client: httpx.AsyncClient, session: AsyncSession, world: World
) -> UUID:
    evaluation_id, _ = await extracted_run(
        app, client, session, world, pdfs.policy_pdf(), analyse=True
    )
    await app.state.container.runner.drain()
    return evaluation_id


def _answers(evaluation_id: UUID, **overrides: Any) -> dict[str, Any]:
    return {
        "evaluation_id": str(evaluation_id),
        "usefulness": 5,
        "ease_of_use": 4,
        "trust_in_results": 4,
        "actionable_recommendations": True,
        "manual_time_hours": 16,
        "system_time_hours": 1.5,
        "willingness_to_use": 5,
        "willingness_to_pay": "MAYBE",
        "comments": "Útil para priorizar.",
        **overrides,
    }


async def test_survey_opens_only_after_approval(
    client: httpx.AsyncClient, world: World, analysed: UUID
) -> None:
    status = await client.get(
        f"/api/v1/evaluations/{analysed}/feedback", headers=world.sme_a.headers
    )
    assert status.json() == {"available": False, "submitted_at": None}
    early = await client.post(
        "/api/v1/feedback", json=_answers(analysed), headers=world.sme_a.headers
    )
    assert early.status_code == 409


async def test_one_answer_per_approved_evaluation(
    app: FastAPI,
    client: httpx.AsyncClient,
    session: AsyncSession,
    world: World,
    analysed: UUID,
) -> None:
    await _approve(app, client, analysed, world)
    first = await client.post(
        "/api/v1/feedback", json=_answers(analysed), headers=world.sme_a.headers
    )
    assert first.status_code == 201, first.text
    assert first.json()["submitted_at"]
    again = await client.post(
        "/api/v1/feedback", json=_answers(analysed), headers=world.sme_a.headers
    )
    assert again.status_code == 409
    row = await session.scalar(select(FeedbackModel))
    assert row is not None
    assert (float(row.manual_time_hours), float(row.system_time_hours)) == (16.0, 1.5)
    assert row.willingness_to_pay == "MAYBE"
    audited = await session.scalar(
        select(func.count())
        .select_from(AuditLogModel)
        .where(AuditLogModel.action == "FEEDBACK_SUBMITTED")
    )
    assert audited == 1


@pytest.mark.parametrize(
    "override",
    [
        {"usefulness": 0},
        {"trust_in_results": 6},
        {"manual_time_hours": -1},
        {"system_time_hours": 1001},
        {"willingness_to_pay": "SURE"},
        {"comments": "x" * 2001},
    ],
)
async def test_invalid_answers_are_rejected(
    app: FastAPI,
    client: httpx.AsyncClient,
    world: World,
    analysed: UUID,
    override: dict[str, Any],
) -> None:
    await _approve(app, client, analysed, world)
    response = await client.post(
        "/api/v1/feedback", json=_answers(analysed, **override), headers=world.sme_a.headers
    )
    assert response.status_code == 422


async def test_only_the_owning_company_answers(
    app: FastAPI, client: httpx.AsyncClient, world: World, analysed: UUID
) -> None:
    await _approve(app, client, analysed, world)
    payload = _answers(analysed)
    assert (
        await client.post("/api/v1/feedback", json=payload, headers=world.sme_b.headers)
    ).status_code == 404
    for actor in (world.reviewer, world.admin, world.mentor):
        response = await client.post("/api/v1/feedback", json=payload, headers=actor.headers)
        assert response.status_code == 403
