from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.analysis.infrastructure.models import AIFindingModel
from auditor.review.infrastructure.models import FinalFindingModel, HumanReviewModel
from tests.support import pdfs
from tests.support.factories import seed_checklist
from tests.support.pipeline import extracted_run
from tests.support.world import World, build_world


@pytest.fixture
async def world(session: AsyncSession) -> World:
    await seed_checklist(session)
    return await build_world(session)


@pytest.fixture
async def reviewed_evaluation(
    app: FastAPI, client: httpx.AsyncClient, session: AsyncSession, world: World
) -> UUID:
    evaluation_id, _ = await extracted_run(
        app, client, session, world, pdfs.policy_pdf(), analyse=True
    )
    await app.state.container.runner.drain()
    return evaluation_id


async def _review(client: httpx.AsyncClient, evaluation_id: UUID, headers: dict[str, str]) -> Any:
    response = await client.get(f"/api/v1/reviews/{evaluation_id}", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def _item(review: Any, code: str) -> Any:
    return next(item for item in review["items"] if item["criterion"]["code"] == code)


async def _review_everything(
    client: httpx.AsyncClient, review: Any, headers: dict[str, str]
) -> None:
    for item in review["items"]:
        if item["review"]["review_status"] != "PENDING_REVIEW":
            continue
        finding = item["finding_id"]
        if item["ai"]["status"] is None:
            response = await client.post(
                f"/api/v1/findings/{finding}/discard",
                json={"comment": "La IA no pudo clasificar este criterio."},
                headers=headers,
            )
        else:
            response = await client.post(
                f"/api/v1/findings/{finding}/approve", json={}, headers=headers
            )
        assert response.status_code == 200, response.text


async def test_reviewer_sees_thirty_findings_with_traceable_evidence(
    client: httpx.AsyncClient, world: World, reviewed_evaluation: UUID
) -> None:
    review = await _review(client, reviewed_evaluation, world.reviewer.headers)
    summary = review["summary"]
    assert summary["total"] == 30
    assert summary["found"] + summary["partial"] + summary["no_evidence"] + summary["errors"] == 30
    assert summary["pending"] == 30
    iso07 = _item(review, "ISO-07")
    assert iso07["criterion"]["name"] == "Gestión de activos"
    assert iso07["ai"]["status"] == "FOUND"
    evidence = iso07["ai"]["evidence"][0]
    assert (evidence["document_name"], evidence["page"], evidence["citation_verified"]) == (
        "documento.pdf",
        3,
        True,
    )
    assert iso07["ai"]["provider"] == "fake"
    attention = [item["ai"]["needs_attention"] for item in review["items"]]
    assert attention == sorted(attention, reverse=True)


async def test_unapproved_ai_findings_are_never_visible_to_the_company(
    client: httpx.AsyncClient, world: World, reviewed_evaluation: UUID
) -> None:
    review = await _review(client, reviewed_evaluation, world.reviewer.headers)
    finding = review["items"][0]["finding_id"]
    for headers in (world.sme_a.headers, world.mentor.headers):
        assert (
            await client.get(f"/api/v1/reviews/{reviewed_evaluation}", headers=headers)
        ).status_code == 403
        assert (await client.get(f"/api/v1/findings/{finding}", headers=headers)).status_code == 403
    other_reviewer = await client.get(
        f"/api/v1/findings/{finding}", headers=world.other_reviewer.headers
    )
    assert other_reviewer.status_code == 404
    approve = await client.post(
        f"/api/v1/findings/{finding}/approve", json={}, headers=world.sme_a.headers
    )
    assert approve.status_code == 403


async def test_three_layers_and_re_review_history(
    client: httpx.AsyncClient, session: AsyncSession, world: World, reviewed_evaluation: UUID
) -> None:
    review = await _review(client, reviewed_evaluation, world.reviewer.headers)
    iso07 = _item(review, "ISO-07")
    finding = iso07["finding_id"]

    approved = await client.post(
        f"/api/v1/findings/{finding}/approve",
        json={"comment": "Correcto"},
        headers=world.reviewer.headers,
    )
    assert approved.json()["review_status"] == "APPROVED"
    edited = await client.patch(
        f"/api/v1/findings/{finding}",
        json={
            "status": "PARTIAL",
            "gap": "Falta la fecha de la última actualización del inventario.",
            "recommendation": "Registrar la fecha y el responsable de cada actualización.",
            "priority": "MEDIUM",
            "effort": "LOW",
            "risk_level": "MEDIUM",
            "comment": "Ajusto el estado a parcial.",
        },
        headers=world.reviewer.headers,
    )
    assert edited.json()["review_status"] == "EDITED_APPROVED"

    ai_status = await session.scalar(
        select(AIFindingModel.status).where(AIFindingModel.id == finding)
    )
    assert ai_status == "FOUND"  # the AI layer is never overwritten
    final = await session.scalar(
        select(FinalFindingModel).where(FinalFindingModel.ai_finding_id == finding)
    )
    assert final is not None
    assert (final.status, final.priority) == ("PARTIAL", "MEDIUM")
    assert final.evidence and final.evidence[0]["page"] == 3
    history = (
        await session.scalars(
            select(HumanReviewModel)
            .where(HumanReviewModel.ai_finding_id == finding)
            .order_by(HumanReviewModel.created_at)
        )
    ).all()
    assert [entry.action for entry in history] == ["APPROVE", "EDIT"]
    assert history[1].previous_values["status"] == "FOUND"
    assert history[1].new_values["status"] == "PARTIAL"

    detail = await client.get(f"/api/v1/findings/{finding}", headers=world.reviewer.headers)
    assert [entry["action"] for entry in detail.json()["history"]] == ["APPROVE", "EDIT"]

    short_discard = await client.post(
        f"/api/v1/findings/{finding}/discard",
        json={"comment": "no"},
        headers=world.reviewer.headers,
    )
    assert short_discard.status_code == 422


async def test_evaluation_is_approved_only_after_every_finding_is_reviewed(
    client: httpx.AsyncClient, session: AsyncSession, world: World, reviewed_evaluation: UUID
) -> None:
    headers = world.reviewer.headers
    early = await client.post(f"/api/v1/evaluations/{reviewed_evaluation}/approve", headers=headers)
    assert early.status_code == 422
    assert "sin revisar" in early.json()["message"]

    await _review_everything(client, await _review(client, reviewed_evaluation, headers), headers)
    approved = await client.post(
        f"/api/v1/evaluations/{reviewed_evaluation}/approve", headers=headers
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"
    assert await session.scalar(select(func.count()).select_from(FinalFindingModel)) == 30

    review = await _review(client, reviewed_evaluation, headers)
    locked = await client.post(
        f"/api/v1/findings/{review['items'][0]['finding_id']}/approve", json={}, headers=headers
    )
    assert locked.status_code == 409
    again = await client.post(
        f"/api/v1/evaluations/{reviewed_evaluation}/reject",
        json={"reason": "Motivo suficientemente largo"},
        headers=headers,
    )
    assert again.status_code == 409


async def test_rejection_requires_a_reason_the_company_can_read(
    client: httpx.AsyncClient, world: World, reviewed_evaluation: UUID
) -> None:
    path = f"/api/v1/evaluations/{reviewed_evaluation}/reject"
    assert (
        await client.post(path, json={"reason": "corto"}, headers=world.reviewer.headers)
    ).status_code == 422
    by_sme = await client.post(
        path, json={"reason": "No corresponde a la empresa"}, headers=world.sme_a.headers
    )
    assert by_sme.status_code == 403
    reason = "Falta la política de continuidad del negocio; carga el documento actualizado."
    rejected = await client.post(path, json={"reason": reason}, headers=world.reviewer.headers)
    assert rejected.json()["status"] == "REJECTED"
    seen_by_sme = await client.get(
        f"/api/v1/evaluations/{reviewed_evaluation}", headers=world.sme_a.headers
    )
    assert seen_by_sme.json()["evaluation"]["rejection_reason"] == reason


async def test_review_queue_lists_assigned_pending_evaluations(
    client: httpx.AsyncClient, world: World, reviewed_evaluation: UUID
) -> None:
    mine = (await client.get("/api/v1/reviews", headers=world.reviewer.headers)).json()
    assert [
        (item["evaluation_id"], item["findings"], item["reviewed"]) for item in mine["items"]
    ] == [(str(reviewed_evaluation), 30, 0)]
    others = (await client.get("/api/v1/reviews", headers=world.other_reviewer.headers)).json()
    assert others["items"] == []
