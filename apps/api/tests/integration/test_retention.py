from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.audit.infrastructure.models import AuditLogModel
from auditor.documents.infrastructure.models import DocumentChunkModel, DocumentModel
from auditor.evaluations.infrastructure.models import EvaluationModel
from auditor.review.infrastructure.models import FinalFindingModel
from auditor.shared.domain.errors import ResourceNotFoundError
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
    return evaluation_id


async def _age(session: AsyncSession, evaluation_id: UUID, days: int) -> None:
    await session.execute(
        update(EvaluationModel)
        .where(EvaluationModel.id == evaluation_id)
        .values(approved_at=datetime.now(UTC) - timedelta(days=days))
    )
    await session.commit()


async def _purge(client: httpx.AsyncClient, world: World) -> dict[str, int]:
    response = await client.post("/api/v1/retention/purge", headers=world.admin.headers)
    assert response.status_code == 200, response.text
    return dict(response.json())


async def test_nothing_is_purged_before_the_retention_period(
    client: httpx.AsyncClient, session: AsyncSession, world: World, approved: UUID
) -> None:
    await _age(session, approved, 89)
    assert await _purge(client, world) == {"evaluations": 0, "documents": 0}
    document = await session.scalar(select(DocumentModel))
    assert document is not None and document.purged_at is None


async def test_expired_documents_are_purged_and_results_are_kept(
    app: FastAPI,
    client: httpx.AsyncClient,
    session: AsyncSession,
    world: World,
    approved: UUID,
) -> None:
    document = await session.scalar(select(DocumentModel))
    assert document is not None and document.storage_path
    path = document.storage_path
    await _age(session, approved, 91)

    assert await _purge(client, world) == {"evaluations": 1, "documents": 1}
    session.expire_all()
    purged = await session.scalar(select(DocumentModel))
    assert purged is not None
    assert (purged.status, purged.storage_path) == ("PURGED", None)
    assert purged.purged_at is not None
    assert await session.scalar(select(func.count()).select_from(DocumentChunkModel)) == 0
    container = app.state.container
    with pytest.raises(ResourceNotFoundError):
        await container.storage.download(container.settings.documents_bucket, path)

    assert await session.scalar(select(func.count()).select_from(FinalFindingModel)) == 30
    results = await client.get(
        f"/api/v1/evaluations/{approved}/findings", headers=world.sme_a.headers
    )
    assert results.status_code == 200
    report = await client.get(f"/api/v1/evaluations/{approved}/report", headers=world.sme_a.headers)
    assert report.json()["state"] == "READY"

    audit = await session.scalar(
        select(AuditLogModel).where(AuditLogModel.action == "RETENTION_PURGED")
    )
    assert audit is not None
    assert audit.resource_id == approved and audit.details["documents"] == 1
    assert await _purge(client, world) == {"evaluations": 0, "documents": 0}


async def test_only_admins_trigger_a_purge(
    client: httpx.AsyncClient, world: World, approved: UUID
) -> None:
    for actor in (world.sme_a, world.reviewer, world.mentor):
        response = await client.post("/api/v1/retention/purge", headers=actor.headers)
        assert response.status_code == 403
