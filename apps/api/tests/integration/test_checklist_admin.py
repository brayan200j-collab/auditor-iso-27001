from __future__ import annotations

from typing import Any

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.support.factories import seed_checklist
from tests.support.world import World, build_world


@pytest.fixture
async def world(session: AsyncSession) -> World:
    await seed_checklist(session)
    return await build_world(session)


def _editable(item: dict[str, Any], **changes: Any) -> dict[str, Any]:
    fields = (
        "name",
        "description",
        "evaluation_question",
        "expected_evidence",
        "iso_reference",
        "cis_reference",
        "nist_reference",
        "reference_status",
        "keywords",
        "priority",
        "risk_level",
        "effort",
        "active",
    )
    body = {
        field: item[field] or "" if field.endswith("_reference") else item[field]
        for field in fields
    }
    body.update(changes)
    return body


async def test_admin_versions_the_checklist(client: httpx.AsyncClient, world: World) -> None:
    headers = world.admin.headers
    versions = (await client.get("/api/v1/checklists", headers=headers)).json()
    assert [(v["version"], v["status"], v["item_count"]) for v in versions] == [
        (1, "PUBLISHED", 30)
    ]

    published = (
        await client.get(f"/api/v1/checklists/{versions[0]['id']}", headers=headers)
    ).json()
    iso07 = next(item for item in published["items"] if item["code"] == "ISO-07")
    immutable = await client.put(
        f"/api/v1/checklists/{published['id']}/items/ISO-07",
        json=_editable(iso07, name="Otro nombre"),
        headers=headers,
    )
    assert immutable.status_code == 409

    draft = await client.post("/api/v1/checklists", headers=headers)
    assert draft.status_code == 201
    draft_body = draft.json()
    assert (draft_body["version"], draft_body["status"], draft_body["item_count"]) == (
        2,
        "DRAFT",
        30,
    )
    second_draft = await client.post("/api/v1/checklists", headers=headers)
    assert second_draft.status_code == 409

    edited = await client.put(
        f"/api/v1/checklists/{draft_body['id']}/items/ISO-07",
        json=_editable(iso07, keywords=["inventario", "CMDB"], reference_status="confirmed"),
        headers=headers,
    )
    assert edited.status_code == 200
    edited_item = next(i for i in edited.json()["items"] if i["code"] == "ISO-07")
    assert edited_item["keywords"] == ["inventario", "CMDB"]
    assert edited_item["reference_status"] == "confirmed"

    publish = await client.post(f"/api/v1/checklists/{draft_body['id']}/publish", headers=headers)
    assert publish.json()["status"] == "PUBLISHED"
    original = (await client.get(f"/api/v1/checklists/{published['id']}", headers=headers)).json()
    original_iso07 = next(item for item in original["items"] if item["code"] == "ISO-07")
    assert original_iso07["keywords"] == iso07["keywords"]


async def test_invalid_item_edits_are_rejected(client: httpx.AsyncClient, world: World) -> None:
    headers = world.admin.headers
    draft = (await client.post("/api/v1/checklists", headers=headers)).json()
    item = draft["items"][0]
    for changes in ({"keywords": []}, {"priority": "URGENTE"}, {"cis_reference": "CIS-1"}):
        response = await client.put(
            f"/api/v1/checklists/{draft['id']}/items/{item['code']}",
            json=_editable(item, **changes),
            headers=headers,
        )
        assert response.status_code == 422, changes
    unknown = await client.put(
        f"/api/v1/checklists/{draft['id']}/items/ISO-99", json=_editable(item), headers=headers
    )
    assert unknown.status_code == 404


@pytest.mark.parametrize("member", ["reviewer", "sme_a", "mentor"])
async def test_only_admins_manage_the_checklist(
    client: httpx.AsyncClient, world: World, member: str
) -> None:
    headers = getattr(world, member).headers
    assert (await client.get("/api/v1/checklists", headers=headers)).status_code == 403
    assert (await client.post("/api/v1/checklists", headers=headers)).status_code == 403
