from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from tests.support import pdfs
from tests.support.factories import seed_checklist
from tests.support.pipeline import extracted_run
from tests.support.world import World, build_world

PRIORITY = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


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


async def _review_all(client: httpx.AsyncClient, evaluation_id: UUID, world: World) -> Any:
    """Edits ISO-07, discards ISO-30, approves the rest, then approves the evaluation."""
    headers = world.reviewer.headers
    review = (await client.get(f"/api/v1/reviews/{evaluation_id}", headers=headers)).json()
    for item in review["items"]:
        finding, code = item["finding_id"], item["criterion"]["code"]
        if code == "ISO-07":
            response = await client.patch(
                f"/api/v1/findings/{finding}",
                json={
                    "status": "PARTIAL",
                    "gap": "Falta el responsable del inventario.",
                    "recommendation": "Asignar un responsable y revisar el inventario cada año.",
                    "priority": "CRITICAL",
                    "effort": "LOW",
                    "risk_level": "HIGH",
                    "comment": "Ajustado por el revisor.",
                },
                headers=headers,
            )
        elif code == "ISO-30" or item["ai"]["status"] is None:
            response = await client.post(
                f"/api/v1/findings/{finding}/discard",
                json={"comment": "No aplica al alcance de esta autoevaluación."},
                headers=headers,
            )
        else:
            response = await client.post(
                f"/api/v1/findings/{finding}/approve", json={}, headers=headers
            )
        assert response.status_code == 200, response.text
    return review


async def test_results_are_hidden_until_the_evaluation_is_approved(
    client: httpx.AsyncClient, world: World, analysed: UUID
) -> None:
    response = await client.get(
        f"/api/v1/evaluations/{analysed}/findings", headers=world.sme_a.headers
    )
    assert response.status_code == 409
    assert response.json()["code"] == "CONFLICT"
    assert "items" not in response.text and "findings" not in response.json()


async def test_company_sees_reviewed_results_with_counts_and_ordered_gaps(
    client: httpx.AsyncClient, world: World, analysed: UUID
) -> None:
    review = await _review_all(client, analysed, world)
    approve = await client.post(
        f"/api/v1/evaluations/{analysed}/approve", headers=world.reviewer.headers
    )
    assert approve.status_code == 200, approve.text

    response = await client.get(
        f"/api/v1/evaluations/{analysed}/findings", headers=world.sme_a.headers
    )
    assert response.status_code == 200, response.text
    results = response.json()
    coverage = results["coverage"]
    assert coverage["total"] == 30
    assert coverage["discarded"] >= 1
    assert (
        coverage["found"] + coverage["partial"] + coverage["no_evidence"] + coverage["discarded"]
        == 30
    )
    assert "%" not in response.text

    findings = {f["criterion"]["code"]: f for f in results["findings"]}
    assert "ISO-30" not in findings
    iso07 = findings["ISO-07"]
    assert (iso07["status"], iso07["priority"], iso07["review_status"]) == (
        "PARTIAL",
        "CRITICAL",
        "EDITED_APPROVED",
    )
    assert iso07["reviewer_comment"] == "Ajustado por el revisor."
    assert all(e["page"] >= 1 and e["document_name"] for e in iso07["evidence"])
    for finding in results["findings"]:
        assert set(finding) >= {"criterion", "status", "evidence"}
        assert "confidence" not in finding and "ai" not in finding

    by_id = {f["finding_id"]: f for f in results["findings"]}
    gaps = [by_id[i] for i in results["gap_ids"]]
    assert all(g["status"] != "FOUND" for g in gaps)
    ranks = [PRIORITY[g["priority"]] for g in gaps]
    assert ranks == sorted(ranks)
    phases = [p["phase"] for p in results["plan"]]
    assert phases == sorted(phases) and phases[0] == 1
    assert iso07["finding_id"] in results["plan"][0]["finding_ids"]
    assert sum(len(p["finding_ids"]) for p in results["plan"]) == len(gaps)

    # Unverified AI quotes never reach the company.
    ai_quotes = {
        e["quote"]
        for item in review["items"]
        for e in item["ai"]["evidence"]
        if not e["citation_verified"]
    }
    company_quotes = {e["quote"] for f in results["findings"] for e in f["evidence"]}
    assert not ai_quotes & company_quotes


async def test_results_respect_company_and_role_scope(
    client: httpx.AsyncClient, world: World, analysed: UUID
) -> None:
    await _review_all(client, analysed, world)
    await client.post(f"/api/v1/evaluations/{analysed}/approve", headers=world.reviewer.headers)
    url = f"/api/v1/evaluations/{analysed}/findings"
    assert (await client.get(url, headers=world.sme_b.headers)).status_code == 404
    assert (await client.get(url, headers=world.other_reviewer.headers)).status_code == 404
    assert (await client.get(url, headers=world.mentor.headers)).status_code == 403
    for actor in (world.admin, world.reviewer):
        assert (await client.get(url, headers=actor.headers)).status_code == 200
