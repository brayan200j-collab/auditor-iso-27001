from __future__ import annotations

import asyncio
from uuid import UUID

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from auditor.analysis.application.ports import LlmRequest, LlmResponse, ProviderUnavailableError
from auditor.analysis.application.retrying_provider import RetryingProvider
from auditor.analysis.infrastructure.models import AIFindingModel
from auditor.audit.infrastructure.models import AuditLogModel
from auditor.evaluations.infrastructure.models import EvaluationModel
from tests.support import pdfs
from tests.support.factories import seed_checklist
from tests.support.pipeline import extracted_run
from tests.support.world import World, build_world


@pytest.fixture
async def world(session: AsyncSession, app: FastAPI) -> World:
    app.state.container.runner._retry_delay = 0
    await seed_checklist(session)
    return await build_world(session)


async def _evaluation(session: AsyncSession, evaluation_id: UUID) -> EvaluationModel:
    session.expire_all()
    model = await session.get(EvaluationModel, evaluation_id)
    assert model is not None
    return model


async def _findings(session: AsyncSession, run_id: UUID) -> dict[str, str | None]:
    rows = await session.execute(
        select(AIFindingModel.criterion_code, AIFindingModel.status).where(
            AIFindingModel.analysis_run_id == run_id
        )
    )
    return dict(rows.all())


class FailingAfter:
    """Delegates to the real test double, then simulates an outage."""

    def __init__(self, inner: object, successes: int) -> None:
        self._inner = inner
        self._left = successes
        self.name = "fake"
        self.model = "fake-deterministic-v1"

    async def complete(self, request: LlmRequest) -> LlmResponse:
        if self._left <= 0:
            raise ProviderUnavailableError("simulated outage")
        self._left -= 1
        return await self._inner.complete(request)  # type: ignore[attr-defined, no-any-return]


async def test_full_analysis_reaches_human_review_with_thirty_findings(
    app: FastAPI,
    client: httpx.AsyncClient,
    session: AsyncSession,
    engine: AsyncEngine,
    world: World,
) -> None:
    evaluation_id, run_id = await extracted_run(
        app, client, session, world, pdfs.policy_pdf(), analyse=True
    )
    await app.state.container.runner.drain()

    evaluation = await _evaluation(session, evaluation_id)
    assert evaluation.status == "PENDING_REVIEW"
    findings = await _findings(session, run_id)
    assert len(findings) == 30
    assert findings["ISO-07"] == "FOUND"
    assert findings["ISO-24"] == "NO_DOCUMENTARY_EVIDENCE"
    generated = await session.scalar(
        select(AuditLogModel.details).where(AuditLogModel.action == "FINDINGS_GENERATED")
    )
    assert generated is not None
    assert generated["findings"] == 30

    async with engine.connect() as connection:
        with pytest.raises(DBAPIError, match="append-only"):
            await connection.execute(
                text("UPDATE ai_findings SET status = 'FOUND' WHERE analysis_run_id = :id"),
                {"id": run_id},
            )


async def test_interrupted_analysis_resumes_without_duplicating_findings(
    app: FastAPI, client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    container = app.state.container
    original = container.llm
    container.llm = RetryingProvider(
        FailingAfter(container.llm_backend, successes=5),
        max_retries=0,
        max_backoff_seconds=0.01,
        semaphore=asyncio.Semaphore(1),
    )
    evaluation_id, run_id = await extracted_run(
        app, client, session, world, pdfs.policy_pdf(), analyse=True
    )
    await container.runner.drain()

    failed = await _evaluation(session, evaluation_id)
    assert (failed.status, failed.failure_reason, failed.failed_stage) == (
        "FAILED",
        "ANALYSIS_ERROR",
        "ANALYZING",
    )
    partial = await _findings(session, run_id)
    assert 0 < len(partial) < 30
    status = (
        await client.get(f"/api/v1/evaluations/{evaluation_id}/status", headers=world.sme_a.headers)
    ).json()
    assert (status["criteria_done"], status["criteria_total"]) == (len(partial), 30)

    container.llm = original
    retry = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/retry", headers=world.reviewer.headers
    )
    assert retry.json()["status"] == "ANALYZING"
    await container.runner.drain()

    assert (await _evaluation(session, evaluation_id)).status == "PENDING_REVIEW"
    total = await session.scalar(
        select(func.count()).where(AIFindingModel.analysis_run_id == run_id)
    )
    assert total == 30
    resumed = await _findings(session, run_id)
    assert {code: resumed[code] for code in partial} == partial


async def test_quota_exhaustion_fails_the_evaluation_clearly(
    app: FastAPI, client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    app.state.container.settings.max_llm_calls_per_evaluation = 3
    evaluation_id, _ = await extracted_run(
        app, client, session, world, pdfs.policy_pdf(), analyse=True
    )
    await app.state.container.runner.drain()
    failed = await _evaluation(session, evaluation_id)
    assert (failed.status, failed.failure_reason) == ("FAILED", "QUOTA_EXCEEDED")
