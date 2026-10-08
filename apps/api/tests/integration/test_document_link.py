from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.audit.infrastructure.models import AuditLogModel
from auditor.documents.infrastructure.models import DocumentModel
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
) -> tuple[UUID, UUID]:
    evaluation_id, _ = await extracted_run(
        app, client, session, world, pdfs.policy_pdf(), analyse=True
    )
    await app.state.container.runner.drain()
    document_id = await session.scalar(select(DocumentModel.id))
    assert document_id is not None
    return evaluation_id, document_id


def _url(ids: tuple[UUID, UUID]) -> str:
    return f"/api/v1/evaluations/{ids[0]}/documents/{ids[1]}/link"


async def test_assigned_reviewer_opens_the_original_pdf_and_it_is_audited(
    client: httpx.AsyncClient, session: AsyncSession, world: World, analysed: tuple[UUID, UUID]
) -> None:
    response = await client.get(_url(analysed), headers=world.reviewer.headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["expires_in"] > 0
    assert "download=" not in body["url"]  # opens inline in the browser's PDF viewer

    viewed = await session.scalar(
        select(AuditLogModel).where(AuditLogModel.action == "DOCUMENT_VIEWED")
    )
    assert viewed is not None
    assert (viewed.actor_id, viewed.resource_id) == (world.reviewer.id, analysed[1])


async def test_only_people_with_access_to_the_evaluation_get_a_link(
    client: httpx.AsyncClient, world: World, analysed: tuple[UUID, UUID]
) -> None:
    assert (await client.get(_url(analysed), headers=world.sme_a.headers)).status_code == 200
    assert (await client.get(_url(analysed), headers=world.admin.headers)).status_code == 200
    for outsider in (world.sme_b, world.other_reviewer):
        assert (await client.get(_url(analysed), headers=outsider.headers)).status_code == 404
    assert (await client.get(_url(analysed), headers=world.mentor.headers)).status_code == 403
    assert (await client.get(_url(analysed))).status_code == 401


async def test_purged_documents_explain_the_retention_policy(
    client: httpx.AsyncClient, session: AsyncSession, world: World, analysed: tuple[UUID, UUID]
) -> None:
    await session.execute(
        update(DocumentModel)
        .where(DocumentModel.id == analysed[1])
        .values(status="PURGED", storage_path=None, purged_at=datetime.now(UTC))
    )
    await session.commit()
    response = await client.get(_url(analysed), headers=world.reviewer.headers)
    assert response.status_code == 409
    assert "política de retención" in response.json()["message"]
