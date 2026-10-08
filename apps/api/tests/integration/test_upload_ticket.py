from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.identity.domain.upload_ticket import issue_ticket, verify_ticket
from auditor.shared.domain.errors import UnauthorizedError
from tests.integration.test_documents_api import _ready_evaluation
from tests.support import pdfs
from tests.support.world import World, build_world

NOW = datetime(2026, 10, 8, 12, 0, tzinfo=UTC)


@pytest.fixture
async def world(session: AsyncSession) -> World:
    return await build_world(session)


def test_ticket_round_trip_and_rejections() -> None:
    user, evaluation, secret = uuid4(), uuid4(), b"k" * 32
    ticket = issue_ticket(secret, user, evaluation, NOW).value
    assert verify_ticket(secret, ticket, evaluation, NOW + timedelta(minutes=4)) == user
    for bad in (
        lambda: verify_ticket(secret, ticket, evaluation, NOW + timedelta(minutes=6)),  # expired
        lambda: verify_ticket(secret, ticket, uuid4(), NOW),  # other evaluation
        lambda: verify_ticket(b"x" * 32, ticket, evaluation, NOW),  # other key
        lambda: verify_ticket(secret, ticket[:-2] + "AA", evaluation, NOW),  # tampered
        lambda: verify_ticket(secret, "garbage", evaluation, NOW),
    ):
        with pytest.raises(UnauthorizedError):
            bad()


async def _ticket(client: httpx.AsyncClient, evaluation_id: object, headers: dict[str, str]):
    return await client.post(
        f"/api/v1/evaluations/{evaluation_id}/documents/upload-ticket", headers=headers
    )


async def test_browser_uploads_directly_with_a_ticket(
    app: FastAPI, client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    evaluation_id = await _ready_evaluation(client, session, world)
    issued = await _ticket(client, evaluation_id, world.sme_a.headers)
    assert issued.status_code == 200, issued.text
    body = issued.json()
    assert body["expires_in"] == 300

    upload = await client.post(
        f"/api/v1/evaluations/{evaluation_id}/documents",
        headers={"x-upload-ticket": body["ticket"]},
        files={"file": ("politica.pdf", pdfs.policy_pdf(), "application/pdf")},
    )
    assert upload.status_code == 201, upload.text
    assert upload.json()["page_count"] == 5


async def test_tickets_are_scoped_to_their_evaluation_and_company(
    app: FastAPI, client: httpx.AsyncClient, session: AsyncSession, world: World
) -> None:
    evaluation_id = await _ready_evaluation(client, session, world)
    # Other company or role: no ticket (generic 404 / 403, like any other operation).
    assert (await _ticket(client, evaluation_id, world.sme_b.headers)).status_code == 404
    assert (await _ticket(client, evaluation_id, world.reviewer.headers)).status_code in {403, 404}
    assert (await _ticket(client, evaluation_id, {})).status_code == 401

    ticket = (await _ticket(client, evaluation_id, world.sme_a.headers)).json()["ticket"]
    for target, headers in (
        (uuid4(), {"x-upload-ticket": ticket}),  # ticket for another evaluation
        (evaluation_id, {"x-upload-ticket": ticket + "x"}),  # tampered
        (evaluation_id, {}),  # neither token nor ticket
    ):
        response = await client.post(
            f"/api/v1/evaluations/{target}/documents",
            headers=headers,
            files={"file": ("politica.pdf", pdfs.policy_pdf(), "application/pdf")},
        )
        assert response.status_code == 401, (target, headers, response.text)


async def test_cors_allows_the_ticket_header_from_the_web_origin(
    client: httpx.AsyncClient,
) -> None:
    response = await client.options(
        f"/api/v1/evaluations/{uuid4()}/documents",
        headers={
            "origin": "http://localhost:3000",
            "access-control-request-method": "POST",
            "access-control-request-headers": "x-upload-ticket",
        },
    )
    assert response.status_code == 200
    assert "x-upload-ticket" in response.headers["access-control-allow-headers"].lower()
