from __future__ import annotations

from pathlib import Path
from uuid import UUID

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.audit.infrastructure.models import AuditLogModel
from auditor.config import Settings
from auditor.evaluations.domain.consent import CURRENT_CONSENT
from auditor.evaluations.infrastructure.models import AnalysisRunModel, EvaluationModel
from auditor.main import create_app
from tests.support import pdfs
from tests.support.factories import create_evaluation
from tests.support.settings import make_settings
from tests.support.world import World, build_world


@pytest.fixture
async def world(session: AsyncSession) -> World:
    return await build_world(session)


async def _ready_evaluation(client: httpx.AsyncClient, session: AsyncSession, world: World) -> UUID:
    evaluation_id = await create_evaluation(session, world.company_a, world.sme_a.id)
    response = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/consent",
        json={"version": CURRENT_CONSENT.version},
        headers=world.sme_a.headers,
    )
    assert response.status_code == 204
    return evaluation_id


async def _upload(
    client: httpx.AsyncClient,
    evaluation_id: UUID,
    headers: dict[str, str],
    data: bytes,
    name: str = "politica.pdf",
    mime: str = "application/pdf",
) -> httpx.Response:
    return await client.post(
        f"/api/v1/evaluations/{evaluation_id}/documents",
        files={"file": (name, data, mime)},
        headers=headers,
    )


async def _status(session: AsyncSession, evaluation_id: UUID) -> str:
    session.expire_all()
    status: str | None = await session.scalar(
        select(EvaluationModel.status).where(EvaluationModel.id == evaluation_id)
    )
    assert status is not None
    return status


async def _actions(session: AsyncSession, action: str) -> list[AuditLogModel]:
    return list(
        (await session.scalars(select(AuditLogModel).where(AuditLogModel.action == action))).all()
    )


async def test_valid_pdf_is_stored_privately_and_moves_the_evaluation(
    client: httpx.AsyncClient, session: AsyncSession, world: World, settings: Settings
) -> None:
    evaluation_id = await _ready_evaluation(client, session, world)
    response = await _upload(client, evaluation_id, world.sme_a.headers, pdfs.policy_pdf())

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["page_count"] == len(pdfs.POLICY_PAGES)
    assert body["has_text"] is True
    assert body["original_name"] == "politica.pdf"
    assert "storage_path" not in body
    assert await _status(session, evaluation_id) == "RECEIVED"

    stored = Path(settings.local_storage_dir) / "documents" / "companies" / str(world.company_a)
    assert len(list(stored.rglob("*.pdf"))) == 1
    assert len(await _actions(session, "DOCUMENT_UPLOADED")) == 1

    listed = await client.get(
        f"/api/v1/evaluations/{evaluation_id}/documents", headers=world.reviewer.headers
    )
    assert listed.status_code == 404  # not assigned to this reviewer
    listed = await client.get(
        f"/api/v1/evaluations/{evaluation_id}/documents", headers=world.sme_a.headers
    )
    assert [doc["id"] for doc in listed.json()] == [body["id"]]


async def test_consent_is_required_before_uploading(
    client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    evaluation_id = await create_evaluation(session, world.company_a, world.sme_a.id)
    response = await _upload(client, evaluation_id, world.sme_a.headers, pdfs.policy_pdf())
    assert response.status_code == 409
    assert "consentimiento" in response.json()["message"]


@pytest.mark.parametrize(
    ("data", "name", "mime", "message"),
    [
        (pdfs.policy_pdf(), "politica.pdf", "text/plain", "no es un PDF válido"),
        (pdfs.policy_pdf(), "politica.exe", "application/pdf", "nombre del archivo"),
        (pdfs.policy_pdf(), "politica.exe.pdf", "application/pdf", "nombre del archivo"),
        (b"MZ\x90\x00 not a pdf", "politica.pdf", "application/pdf", "no es un PDF válido"),
        (pdfs.scanned_pdf(), "escaneado.pdf", "application/pdf", "no admite OCR"),
        (pdfs.encrypted_pdf(), "cifrado.pdf", "application/pdf", "protegido con contraseña"),
        (pdfs.javascript_pdf(), "activo.pdf", "application/pdf", "contenido activo"),
        (pdfs.attachment_pdf(), "adjunto.pdf", "application/pdf", "contenido activo"),
        (pdfs.many_pages_pdf(31), "largo.pdf", "application/pdf", "30 páginas"),
        (pdfs.corrupt_pdf(), "danado.pdf", "application/pdf", "PDF"),
        (b"", "vacio.pdf", "application/pdf", "vacío"),
    ],
)
async def test_invalid_files_are_rejected_and_audited(
    client: httpx.AsyncClient,
    session: AsyncSession,
    world: World,
    data: bytes,
    name: str,
    mime: str,
    message: str,
) -> None:
    evaluation_id = await _ready_evaluation(client, session, world)
    response = await _upload(client, evaluation_id, world.sme_a.headers, data, name, mime)
    assert response.status_code == 422, response.text
    assert response.json()["code"] == "INVALID_FILE"
    assert message in response.json()["message"]
    assert await _status(session, evaluation_id) == "DRAFT"
    assert len(await _actions(session, "DOCUMENT_REJECTED")) == 1


async def test_oversized_bodies_are_cut_off_while_streaming(
    database_url: str, tmp_path: Path, session: AsyncSession, world: World
) -> None:
    settings = make_settings(tmp_storage=tmp_path, database_url=database_url, max_upload_bytes=2048)
    app: FastAPI = create_app(settings)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        evaluation_id = await _ready_evaluation(client, session, world)
        response = await _upload(
            client, evaluation_id, world.sme_a.headers, b"%PDF-" + b"0" * 200_000
        )
    assert response.status_code == 413
    assert response.json()["code"] == "PAYLOAD_TOO_LARGE"


async def test_uploads_respect_tenancy_and_roles(
    client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    evaluation_id = await _ready_evaluation(client, session, world)
    other_company = await _upload(client, evaluation_id, world.sme_b.headers, pdfs.policy_pdf())
    reviewer = await _upload(client, evaluation_id, world.admin.headers, pdfs.policy_pdf())
    assert other_company.status_code == 404
    assert reviewer.status_code == 403


async def test_document_limit_per_evaluation(
    app: FastAPI, client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    app.state.container.settings.max_documents_per_evaluation = 2
    evaluation_id = await _ready_evaluation(client, session, world)
    for _ in range(2):
        assert (
            await _upload(client, evaluation_id, world.sme_a.headers, pdfs.policy_pdf())
        ).status_code == 201
    third = await _upload(client, evaluation_id, world.sme_a.headers, pdfs.policy_pdf())
    assert third.status_code == 429


async def test_deleting_the_last_document_returns_to_draft(
    client: httpx.AsyncClient, session: AsyncSession, world: World, settings: Settings
) -> None:
    evaluation_id = await _ready_evaluation(client, session, world)
    document_id = (
        await _upload(client, evaluation_id, world.sme_a.headers, pdfs.policy_pdf())
    ).json()["id"]

    foreign = await client.delete(
        f"/api/v1/evaluations/{evaluation_id}/documents/{document_id}", headers=world.sme_b.headers
    )
    assert foreign.status_code == 404
    deleted = await client.delete(
        f"/api/v1/evaluations/{evaluation_id}/documents/{document_id}", headers=world.sme_a.headers
    )
    assert deleted.status_code == 204
    assert await _status(session, evaluation_id) == "DRAFT"
    assert not list(Path(settings.local_storage_dir).rglob("*.pdf"))
    assert len(await _actions(session, "DOCUMENT_DELETED")) == 1


async def test_documents_cannot_be_deleted_once_processing(
    client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    evaluation_id = await _ready_evaluation(client, session, world)
    document_id = (
        await _upload(client, evaluation_id, world.sme_a.headers, pdfs.policy_pdf())
    ).json()["id"]
    await session.execute(
        update(EvaluationModel)
        .where(EvaluationModel.id == evaluation_id)
        .values(status="EXTRACTING")
    )
    await session.commit()
    response = await client.delete(
        f"/api/v1/evaluations/{evaluation_id}/documents/{document_id}", headers=world.sme_a.headers
    )
    assert response.status_code == 409


async def test_new_pdf_after_rejection_opens_a_new_analysis_run(
    client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    evaluation_id = await _ready_evaluation(client, session, world)
    await _upload(client, evaluation_id, world.sme_a.headers, pdfs.policy_pdf())
    await session.execute(
        update(EvaluationModel)
        .where(EvaluationModel.id == evaluation_id)
        .values(status="REJECTED", rejection_reason="Falta información de continuidad.")
    )
    await session.commit()

    response = await _upload(
        client, evaluation_id, world.sme_a.headers, pdfs.policy_pdf(), "v2.pdf"
    )
    assert response.status_code == 201
    assert await _status(session, evaluation_id) == "RECEIVED"
    runs = (
        await session.scalars(
            select(AnalysisRunModel.run_number).where(
                AnalysisRunModel.evaluation_id == evaluation_id
            )
        )
    ).all()
    assert sorted(runs) == [1, 2]
    listed = await client.get(
        f"/api/v1/evaluations/{evaluation_id}/documents", headers=world.sme_a.headers
    )
    assert [doc["original_name"] for doc in listed.json()] == ["v2.pdf"]
