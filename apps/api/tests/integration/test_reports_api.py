from __future__ import annotations

from uuid import UUID

import fitz
import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.audit.infrastructure.models import AuditLogModel
from auditor.reports.infrastructure.models import ReportModel
from tests.integration.test_results_api import _review_all
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


async def _approve(
    app: FastAPI, client: httpx.AsyncClient, evaluation_id: UUID, world: World
) -> None:
    await _review_all(client, evaluation_id, world)
    response = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/approve", headers=world.reviewer.headers
    )
    assert response.status_code == 200, response.text
    await app.state.container.runner.drain()


async def _pdf_text(app: FastAPI, session: AsyncSession, evaluation_id: UUID) -> str:
    report = await session.scalar(
        select(ReportModel).where(ReportModel.evaluation_id == evaluation_id)
    )
    assert report is not None
    data = await app.state.container.storage.download(
        app.state.container.settings.reports_bucket, report.storage_path
    )
    assert data.startswith(b"%PDF-")
    with fitz.open(stream=data, filetype="pdf") as document:
        return "\n".join(page.get_text() for page in document)


async def test_no_report_before_approval(
    client: httpx.AsyncClient, world: World, analysed: UUID
) -> None:
    url = f"/api/v1/evaluations/{analysed}/report"
    response = await client.post(url, headers=world.reviewer.headers)
    assert response.status_code == 409
    status = await client.get(url, headers=world.sme_a.headers)
    assert status.json()["state"] == "NONE"


async def test_approval_generates_a_traceable_pdf_report(
    app: FastAPI,
    client: httpx.AsyncClient,
    session: AsyncSession,
    world: World,
    analysed: UUID,
) -> None:
    await _approve(app, client, analysed, world)

    status = await client.get(f"/api/v1/evaluations/{analysed}/report", headers=world.sme_a.headers)
    assert status.status_code == 200, status.text
    body = status.json()
    assert (body["state"], body["version"]) == ("READY", 1)

    # Lines may wrap after a slash ("ISO/ IEC"); normalize whitespace before comparing.
    text = " ".join((await _pdf_text(app, session, analysed)).split()).replace("/ ", "/")
    for expected in (
        "Informe de autoevaluación inicial",
        "Cobertura documental preliminar",
        "de 30 criterios con evidencia documental",
        "Plan inicial de mejora",
        "ISO-07 · Gestión de activos",
        "Página 3",
        "Ajustado por el revisor.",
        "no constituye una certificación ISO/IEC 27001",
        "proveedor externo de inferencia",
        "documento.pdf",
    ):
        assert expected in text, expected
    for forbidden in ("%", "cumplimiento", "Compliance", "Cumple ISO", "confianza"):
        assert forbidden not in text, forbidden


async def test_download_uses_a_signed_url_and_is_audited(
    app: FastAPI,
    client: httpx.AsyncClient,
    session: AsyncSession,
    world: World,
    analysed: UUID,
) -> None:
    await _approve(app, client, analysed, world)
    report_id = (
        await client.get(f"/api/v1/evaluations/{analysed}/report", headers=world.sme_a.headers)
    ).json()["report_id"]
    url = f"/api/v1/reports/{report_id}/download"

    response = await client.get(url, headers=world.sme_a.headers)
    assert response.status_code == 200, response.text
    signed = response.json()
    assert signed["expires_in"] == app.state.container.settings.signed_url_ttl_seconds
    assert signed["url"].startswith("http")

    assert (await client.get(url, headers=world.sme_b.headers)).status_code == 404
    assert (await client.get(url, headers=world.other_reviewer.headers)).status_code == 404
    assert (await client.get(url, headers=world.mentor.headers)).status_code == 403

    downloads = await session.scalars(
        select(AuditLogModel).where(AuditLogModel.action == "REPORT_DOWNLOADED")
    )
    assert [log.actor_id for log in downloads] == [world.sme_a.id]
    generated = await session.scalars(
        select(AuditLogModel).where(AuditLogModel.action == "REPORT_GENERATED")
    )
    assert len(list(generated)) == 1


async def test_report_generation_is_idempotent_per_run(
    app: FastAPI,
    client: httpx.AsyncClient,
    session: AsyncSession,
    world: World,
    analysed: UUID,
) -> None:
    await _approve(app, client, analysed, world)
    again = await client.post(
        f"/api/v1/evaluations/{analysed}/report", headers=world.reviewer.headers
    )
    assert again.status_code == 202, again.text
    await app.state.container.runner.drain()
    reports = list(
        await session.scalars(select(ReportModel).where(ReportModel.evaluation_id == analysed))
    )
    assert len(reports) == 1
    sme = await client.post(f"/api/v1/evaluations/{analysed}/report", headers=world.sme_a.headers)
    assert sme.status_code == 403
