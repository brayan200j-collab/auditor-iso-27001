"""Helpers that drive the real pipeline (upload → start → extraction) for integration tests."""

from __future__ import annotations

from uuid import UUID

import httpx
from fastapi import FastAPI
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.evaluations.domain.consent import CURRENT_CONSENT
from auditor.evaluations.infrastructure.models import AnalysisRunModel, EvaluationModel
from auditor.shared.application.jobs import JobRecord, PermanentJobError
from auditor.shared.domain.vocabulary import JobKind
from tests.support.factories import create_evaluation
from tests.support.world import World


async def extracted_run(
    app: FastAPI,
    client: httpx.AsyncClient,
    session: AsyncSession,
    world: World,
    pdf: bytes,
    *,
    analyse: bool = False,
) -> tuple[UUID, UUID]:
    """Returns (evaluation_id, analysis_run_id) after a real extraction of `pdf`.

    With `analyse=False` the AI analysis job is left queued so tests can drive the engine.
    """
    runner = app.state.container.runner
    if not analyse:

        async def hold(_job: JobRecord) -> None:
            raise PermanentJobError("HELD_BY_TEST")

        runner.register(JobKind.ANALYSIS, hold)
    evaluation_id = await create_evaluation(
        session, world.company_a, world.sme_a.id, reviewer_id=world.reviewer.id
    )
    headers = world.sme_a.headers
    await client.post(
        f"/api/v1/evaluations/{evaluation_id}/consent",
        json={"version": CURRENT_CONSENT.version},
        headers=headers,
    )
    upload = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/documents",
        files={"file": ("documento.pdf", pdf, "application/pdf")},
        headers=headers,
    )
    assert upload.status_code == 201, upload.text
    started = await client.post(f"/api/v1/evaluations/{evaluation_id}/start", headers=headers)
    assert started.status_code == 202, started.text
    await runner.drain()
    if not analyse:
        app.state.container.register_jobs()
        await session.execute(
            update(EvaluationModel)
            .where(EvaluationModel.id == evaluation_id)
            .values(status="ANALYZING", failure_reason=None, failed_stage=None)
        )
        await session.commit()
    run_id = await session.scalar(
        select(AnalysisRunModel.id).where(AnalysisRunModel.evaluation_id == evaluation_id)
    )
    assert run_id is not None
    return evaluation_id, run_id
