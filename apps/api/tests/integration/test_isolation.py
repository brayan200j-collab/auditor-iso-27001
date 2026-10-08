"""Company isolation (CLAUDE.md section 8.6): walks every operation of the OpenAPI document.

Company A owns a fully processed and approved evaluation (document, findings, report). Company
B's SME and a reviewer not assigned to it replay every operation with A's identifiers and valid
bodies: tenant operations must answer 403/404, the few self-scoped operations may succeed but
must not reveal anything of A, and A's data must be unchanged afterwards.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.audit.infrastructure.models import AuditLogModel
from auditor.checklist.infrastructure.models import ChecklistVersionModel
from auditor.documents.infrastructure.models import DocumentModel
from auditor.reports.infrastructure.models import ReportModel
from auditor.review.infrastructure.models import FinalFindingModel
from tests.integration.test_reports_api import _approve
from tests.support import pdfs
from tests.support.factories import seed_checklist
from tests.support.pipeline import extracted_run
from tests.support.world import Member, World, build_world

PUBLIC = {"/healthz", "/readyz"}
# Operations scoped to the caller's own session or company: they may succeed for an outsider,
# but their responses must not contain anything that belongs to company A.
SELF_SCOPED = {
    ("GET", "/api/v1/me"),
    ("POST", "/api/v1/auth/login-event"),
    ("POST", "/api/v1/auth/logout-event"),
    ("GET", "/api/v1/consent"),
    ("POST", "/api/v1/evaluations"),
    ("GET", "/api/v1/evaluations"),
    ("GET", "/api/v1/reviews"),
    ("GET", "/api/v1/dashboard"),
}


@dataclass(frozen=True)
class Victim:
    evaluation_id: UUID
    document_id: UUID
    finding_id: UUID
    report_id: UUID
    version_id: UUID
    company_id: UUID
    user_id: UUID
    title: str


@pytest.fixture
async def world(session: AsyncSession) -> World:
    await seed_checklist(session)
    return await build_world(session)


@pytest.fixture
async def victim(
    app: FastAPI, client: httpx.AsyncClient, session: AsyncSession, world: World
) -> Victim:
    evaluation_id, _ = await extracted_run(
        app, client, session, world, pdfs.policy_pdf(), analyse=True
    )
    await app.state.container.runner.drain()
    await _approve(app, client, evaluation_id, world)
    detail = (
        await client.get(f"/api/v1/evaluations/{evaluation_id}", headers=world.sme_a.headers)
    ).json()
    document = await session.scalar(select(DocumentModel.id))
    finding = await session.scalar(select(FinalFindingModel.ai_finding_id))
    report = await session.scalar(select(ReportModel.id))
    version = await session.scalar(select(ChecklistVersionModel.id))
    assert document and finding and report and version
    return Victim(
        evaluation_id=evaluation_id,
        document_id=document,
        finding_id=finding,
        report_id=report,
        version_id=version,
        company_id=world.company_a,
        user_id=world.sme_a.id,
        title=detail["evaluation"]["title"],
    )


def _operations(app: FastAPI) -> list[tuple[str, str]]:
    schema: dict[str, Any] = app.openapi()
    return [
        (method.upper(), path)
        for path, methods in schema["paths"].items()
        for method in methods
        if path not in PUBLIC
    ]


def _url(path: str, v: Victim) -> str:
    values = {
        "{evaluation_id}": v.evaluation_id,
        "{document_id}": v.document_id,
        "{finding_id}": v.finding_id,
        "{report_id}": v.report_id,
        "{version_id}": v.version_id,
        "{company_id}": v.company_id,
        "{user_id}": v.user_id,
        "{code}": "ISO-07",
    }
    for placeholder, value in values.items():
        path = path.replace(placeholder, str(value))
    assert "{" not in path, f"unmapped path parameter in {path}"
    return path


def _request(method: str, path: str, v: Victim, world: World) -> dict[str, Any]:
    """Valid payloads, so a rejection can only come from authorization."""
    bodies: dict[tuple[str, str], Any] = {
        ("POST", "/api/v1/users"): {
            "email": "intruso@empresa-b.test",
            "full_name": "Intruso",
            "role": "SME",
            "company_id": str(v.company_id),
        },
        ("PATCH", "/api/v1/users/{user_id}"): {"active": False},
        ("POST", "/api/v1/companies"): {"name": "Empresa intrusa"},
        ("PATCH", "/api/v1/companies/{company_id}"): {"name": "Renombrada", "active": False},
        ("POST", "/api/v1/evaluations"): {"title": "Evaluación propia de B"},
        ("POST", "/api/v1/evaluations/{evaluation_id}/consent"): {"version": "2026-10-v1"},
        ("PUT", "/api/v1/evaluations/{evaluation_id}/reviewer"): {
            "reviewer_id": str(world.other_reviewer.id)
        },
        ("PUT", "/api/v1/checklists/{version_id}/items/{code}"): {
            "name": "Gestión de activos",
            "description": "Descripción propia del criterio.",
            "evaluation_question": "¿Existe un inventario?",
            "expected_evidence": "Inventario",
            "keywords": ["inventario"],
            "priority": "HIGH",
            "risk_level": "HIGH",
            "effort": "MEDIUM",
        },
        ("PATCH", "/api/v1/findings/{finding_id}"): {
            "status": "FOUND",
            "gap": "Brecha alterada",
            "recommendation": "Recomendación alterada",
            "priority": "LOW",
            "effort": "LOW",
            "risk_level": "LOW",
        },
        ("POST", "/api/v1/findings/{finding_id}/approve"): {},
        ("POST", "/api/v1/findings/{finding_id}/discard"): {"comment": "Descartado por intruso"},
        ("POST", "/api/v1/evaluations/{evaluation_id}/reject"): {
            "reason": "Rechazo malicioso de otra empresa"
        },
        ("POST", "/api/v1/feedback"): {
            "evaluation_id": str(v.evaluation_id),
            "usefulness": 1,
            "ease_of_use": 1,
            "trust_in_results": 1,
            "actionable_recommendations": False,
            "manual_time_hours": 1,
            "system_time_hours": 1,
            "willingness_to_use": 1,
            "willingness_to_pay": "NO",
        },
    }
    if (method, path) == ("POST", "/api/v1/evaluations/{evaluation_id}/documents"):
        return {"files": {"file": ("intruso.pdf", pdfs.policy_pdf(), "application/pdf")}}
    if (method, path) in bodies:
        return {"json": bodies[(method, path)]}
    return {}


def _secrets_of(v: Victim) -> list[str]:
    return [
        str(v.evaluation_id),
        str(v.document_id),
        str(v.finding_id),
        str(v.report_id),
        str(v.company_id),
        v.title,
        "documento.pdf",
    ]


@pytest.mark.parametrize("attacker", ["sme_b", "other_reviewer"])
async def test_company_b_never_reaches_company_a(
    app: FastAPI,
    client: httpx.AsyncClient,
    session: AsyncSession,
    world: World,
    victim: Victim,
    attacker: str,
) -> None:
    intruder: Member = getattr(world, attacker)
    operations = _operations(app)
    assert len(operations) > 40, "the walker must cover the whole API"
    failures: list[str] = []
    for method, path in operations:
        response = await client.request(
            method,
            _url(path, victim),
            headers=intruder.headers,
            **_request(method, path, victim, world),
        )
        status = response.status_code
        label = f"{method} {path} -> {status}"
        if (method, path) in SELF_SCOPED:
            leaked = [s for s in _secrets_of(victim) if s in response.text]
            if status >= 500 or leaked:
                failures.append(f"{label} leaked {leaked}")
        elif status not in {403, 404}:
            failures.append(f"{label} {response.text[:120]}")
    await app.state.container.runner.drain()
    assert failures == []

    # Company A's data is untouched.
    owner = world.sme_a.headers
    evaluation = (
        await client.get(f"/api/v1/evaluations/{victim.evaluation_id}", headers=owner)
    ).json()
    assert evaluation["evaluation"]["status"] == "APPROVED"
    documents = (
        await client.get(f"/api/v1/evaluations/{victim.evaluation_id}/documents", headers=owner)
    ).json()
    assert [d["id"] for d in documents] == [str(victim.document_id)]
    results = (
        await client.get(f"/api/v1/evaluations/{victim.evaluation_id}/findings", headers=owner)
    ).json()
    finding = next(f for f in results["findings"] if f["finding_id"] == str(victim.finding_id))
    assert finding["gap"] != "Brecha alterada"
    assert await session.scalar(select(func.count()).select_from(ReportModel)) == 1
    feedback = await client.get(
        f"/api/v1/evaluations/{victim.evaluation_id}/feedback", headers=owner
    )
    assert feedback.json()["submitted_at"] is None
    denied = await session.scalar(
        select(func.count())
        .select_from(AuditLogModel)
        .where(AuditLogModel.action == "ACCESS_DENIED", AuditLogModel.actor_id == intruder.id)
    )
    assert denied and denied > 0
