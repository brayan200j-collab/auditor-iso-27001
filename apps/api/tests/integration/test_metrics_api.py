from __future__ import annotations

from uuid import UUID

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.test_feedback_api import _answers
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
async def approved(
    app: FastAPI, client: httpx.AsyncClient, session: AsyncSession, world: World
) -> UUID:
    evaluation_id, _ = await extracted_run(
        app, client, session, world, pdfs.policy_pdf(), analyse=True
    )
    await app.state.container.runner.drain()
    await _approve(app, client, evaluation_id, world)
    response = await client.post(
        "/api/v1/feedback", json=_answers(evaluation_id), headers=world.sme_a.headers
    )
    assert response.status_code == 201, response.text
    return evaluation_id


async def test_metrics_without_data_say_nothing(client: httpx.AsyncClient, world: World) -> None:
    response = await client.get("/api/v1/metrics", headers=world.admin.headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["technical"]["processed_ok_ratio"] is None
    assert body["technical"]["average_analysis_seconds"] is None
    assert body["value"]["responses"] == 0
    assert body["value"]["average_usefulness"] is None


async def test_pilot_metrics_aggregate_real_activity(
    client: httpx.AsyncClient, world: World, approved: UUID
) -> None:
    body = (await client.get("/api/v1/metrics", headers=world.admin.headers)).json()
    tech, value = body["technical"], body["value"]
    assert body["anonymized"] is False
    assert tech["documents_processed_ok"] == 1
    assert tech["processed_ok_ratio"] == 1.0
    assert tech["average_analysis_seconds"] is not None
    assert tech["llm_calls"] > 0 and tech["approximate_tokens"] > 0
    assert tech["findings_reviewed"] == 30
    assert tech["findings_modified"] >= 2  # ISO-07 edited, ISO-30 discarded
    assert value["responses"] == 1
    assert (value["average_manual_hours"], value["average_system_hours"]) == (16.0, 1.5)
    assert value["average_usefulness"] == 5.0
    assert value["pay_maybe"] == 1


async def test_mentor_sees_only_anonymized_aggregates(
    client: httpx.AsyncClient, world: World, approved: UUID
) -> None:
    response = await client.get("/api/v1/metrics", headers=world.mentor.headers)
    assert response.status_code == 200
    assert response.json()["anonymized"] is True
    text = response.text
    for identifier in (str(approved), str(world.company_a), str(world.sme_a.id)):
        assert identifier not in text
    assert (await client.get("/api/v1/dashboard", headers=world.mentor.headers)).status_code == 403
    for actor in (world.sme_a, world.reviewer):
        assert (await client.get("/api/v1/metrics", headers=actor.headers)).status_code == 403


async def test_dashboard_counts_are_scoped_by_role(
    client: httpx.AsyncClient, world: World, approved: UUID
) -> None:
    async def counts(headers: dict[str, str]) -> dict[str, int]:
        response = await client.get("/api/v1/dashboard", headers=headers)
        assert response.status_code == 200, response.text
        return dict(response.json())

    for actor in (world.sme_a, world.reviewer, world.admin):
        body = await counts(actor.headers)
        assert body["approved"] == 1
        assert body["documents_processed"] == 1
        assert body["high_priority_findings"] >= 1
    for outsider in (world.sme_b, world.other_reviewer):
        body = await counts(outsider.headers)
        assert body == {
            "active_evaluations": 0,
            "pending_review": 0,
            "approved": 0,
            "documents_processed": 0,
            "high_priority_findings": 0,
        }
