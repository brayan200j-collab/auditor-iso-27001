from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.documents.infrastructure.models import DocumentChunkModel, DocumentModel
from auditor.evaluations.domain.consent import CURRENT_CONSENT
from auditor.evaluations.infrastructure.models import EvaluationModel
from auditor.shared.infrastructure.jobs_model import ProcessingJobModel
from tests.support import pdfs
from tests.support.factories import create_evaluation, seed_checklist
from tests.support.world import World, build_world


@pytest.fixture
async def world(session: AsyncSession) -> World:
    await seed_checklist(session)
    return await build_world(session)


async def _received_evaluation(
    client: httpx.AsyncClient, session: AsyncSession, world: World, reviewer: bool = True
) -> UUID:
    evaluation_id = await create_evaluation(
        session,
        world.company_a,
        world.sme_a.id,
        reviewer_id=world.reviewer.id if reviewer else None,
    )
    headers = world.sme_a.headers
    await client.post(
        f"/api/v1/evaluations/{evaluation_id}/consent",
        json={"version": CURRENT_CONSENT.version},
        headers=headers,
    )
    upload = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/documents",
        files={"file": ("politica.pdf", pdfs.policy_pdf(), "application/pdf")},
        headers=headers,
    )
    assert upload.status_code == 201
    return evaluation_id


async def _evaluation(session: AsyncSession, evaluation_id: UUID) -> EvaluationModel:
    session.expire_all()
    model = await session.get(EvaluationModel, evaluation_id)
    assert model is not None
    return model


async def _drain(app: FastAPI) -> None:
    await app.state.container.runner.drain()


async def test_start_extracts_chunks_and_moves_to_analysis(
    app: FastAPI, client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    evaluation_id = await _received_evaluation(client, session, world)
    response = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/start", headers=world.sme_a.headers
    )
    assert response.status_code == 202
    assert response.json()["status"] == "EXTRACTING"

    await _drain(app)

    evaluation = await _evaluation(session, evaluation_id)
    assert evaluation.status == "ANALYZING"
    pages = (
        await session.scalars(
            select(DocumentChunkModel.page).where(DocumentChunkModel.evaluation_id == evaluation_id)
        )
    ).all()
    assert set(pages) == set(range(1, len(pdfs.POLICY_PAGES) + 1))
    document_status = await session.scalar(
        select(DocumentModel.status).where(DocumentModel.evaluation_id == evaluation_id)
    )
    assert document_status == "EXTRACTED"
    jobs = dict(
        (
            await session.execute(
                select(ProcessingJobModel.kind, ProcessingJobModel.status).where(
                    ProcessingJobModel.evaluation_id == evaluation_id
                )
            )
        ).all()
    )
    assert jobs["EXTRACTION"] == "SUCCEEDED"
    assert jobs["ANALYSIS"] in {"QUEUED", "RUNNING"}


async def test_spanish_full_text_search_finds_the_asset_inventory_on_page_three(
    app: FastAPI, client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    evaluation_id = await _received_evaluation(client, session, world)
    await client.post(f"/api/v1/evaluations/{evaluation_id}/start", headers=world.sme_a.headers)
    await _drain(app)
    rows = (
        await session.execute(
            text(
                "SELECT page, section FROM document_chunks WHERE evaluation_id = :id "
                "AND search_vector @@ plainto_tsquery('spanish', 'inventarios de activos') "
                "ORDER BY ts_rank_cd(search_vector, plainto_tsquery('spanish', "
                "'inventarios de activos')) DESC"
            ),
            {"id": evaluation_id},
        )
    ).all()
    assert rows[0] == (3, "5. Gestión de activos")


async def test_extraction_is_idempotent(
    app: FastAPI, client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    from auditor.analysis.application.run_extraction_step import RunExtractionStep
    from auditor.shared.infrastructure.jobs import SqlJobRepository

    evaluation_id = await _received_evaluation(client, session, world)
    await client.post(f"/api/v1/evaluations/{evaluation_id}/start", headers=world.sme_a.headers)
    await _drain(app)
    count = select(func.count()).where(DocumentChunkModel.evaluation_id == evaluation_id)
    before = await session.scalar(count)

    await session.execute(
        update(EvaluationModel)
        .where(EvaluationModel.id == evaluation_id)
        .values(status="EXTRACTING")
    )
    await session.execute(
        update(DocumentModel)
        .where(DocumentModel.evaluation_id == evaluation_id)
        .values(status="STORED")
    )
    await session.commit()
    job_id = await session.scalar(
        select(ProcessingJobModel.id).where(
            ProcessingJobModel.evaluation_id == evaluation_id,
            ProcessingJobModel.kind == "EXTRACTION",
        )
    )
    container = app.state.container
    async with container.scope() as scope:
        job = await SqlJobRepository(scope.session).get(job_id)
        assert job is not None
        await scope.resolve(RunExtractionStep).execute(job)
    await _drain(app)
    assert await session.scalar(count) == before


async def test_start_rules(client: httpx.AsyncClient, session: AsyncSession, world: World) -> None:
    empty = await create_evaluation(session, world.company_a, world.sme_a.id)
    no_documents = await client.post(
        f"/api/v1/evaluations/{empty}/start", headers=world.sme_a.headers
    )
    assert no_documents.status_code == 409

    evaluation_id = await _received_evaluation(client, session, world)
    by_reviewer = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/start", headers=world.reviewer.headers
    )
    by_other_company = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/start", headers=world.sme_b.headers
    )
    assert by_reviewer.status_code == 403
    assert by_other_company.status_code == 404


async def test_unreadable_document_fails_and_can_be_retried(
    app: FastAPI,
    client: httpx.AsyncClient,
    session: AsyncSession,
    world: World,
    settings: object,
) -> None:
    evaluation_id = await _received_evaluation(client, session, world)
    stored = next(Path(settings.local_storage_dir).rglob("*.pdf"))  # type: ignore[attr-defined]
    original = stored.read_bytes()
    stored.write_bytes(pdfs.corrupt_pdf())

    await client.post(f"/api/v1/evaluations/{evaluation_id}/start", headers=world.sme_a.headers)
    await _drain(app)
    failed = await _evaluation(session, evaluation_id)
    assert (failed.status, failed.failure_reason, failed.failed_stage) == (
        "FAILED",
        "EXTRACTION_ERROR",
        "EXTRACTING",
    )
    status_body = (
        await client.get(f"/api/v1/evaluations/{evaluation_id}/status", headers=world.sme_a.headers)
    ).json()
    assert [step["state"] for step in status_body["progress"]][:2] == ["DONE", "FAILED"]

    by_sme = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/retry", headers=world.sme_a.headers
    )
    assert by_sme.status_code == 403

    stored.write_bytes(original)
    retry = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/retry", headers=world.reviewer.headers
    )
    assert retry.status_code == 202
    assert retry.json()["status"] == "EXTRACTING"
    await _drain(app)
    assert (await _evaluation(session, evaluation_id)).status == "ANALYZING"


async def test_recovery_resumes_stale_jobs_and_fails_exhausted_ones(
    app: FastAPI, client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    resumable = await _received_evaluation(client, session, world)
    exhausted = await _received_evaluation(client, session, world)
    for evaluation_id in (resumable, exhausted):
        await client.post(f"/api/v1/evaluations/{evaluation_id}/start", headers=world.sme_a.headers)
    # Simulate a crash: the in-process tasks disappear while the rows say RUNNING.
    await app.state.container.runner.stop()
    long_ago = datetime.now(UTC) - timedelta(hours=2)
    await session.execute(
        update(ProcessingJobModel)
        .where(ProcessingJobModel.evaluation_id == resumable)
        .values(status="RUNNING", attempts=1, heartbeat_at=long_ago)
    )
    await session.execute(
        update(ProcessingJobModel)
        .where(ProcessingJobModel.evaluation_id == exhausted)
        .values(status="RUNNING", attempts=3, max_attempts=3, heartbeat_at=long_ago)
    )
    await session.execute(
        update(EvaluationModel)
        .where(EvaluationModel.id.in_([resumable, exhausted]))
        .values(status="EXTRACTING")
    )
    await session.commit()

    await app.state.container.runner.recover()
    await _drain(app)

    assert (await _evaluation(session, resumable)).status == "ANALYZING"
    failed = await _evaluation(session, exhausted)
    assert (failed.status, failed.failure_reason) == ("FAILED", "INTERRUPTED")
