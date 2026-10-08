from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from auditor.checklist.application.definitions import ChecklistDefinition
from auditor.checklist.domain.entities import ReferenceStatus
from auditor.checklist.infrastructure.yaml_loader import load_checklist_definition

SEED = Path(__file__).resolve().parents[4] / "seeds" / "checklist_v1.yaml"
FORBIDDEN = re.compile(
    r"cumplimiento|compliance|\bcertificad[oa]\b|cumple iso|auditor[ií]a iso autom", re.IGNORECASE
)


@pytest.fixture(scope="module")
def definition() -> ChecklistDefinition:
    return load_checklist_definition(SEED)


def test_seed_has_thirty_ordered_criteria(definition: ChecklistDefinition) -> None:
    assert [item.code for item in definition.items] == [f"ISO-{n:02d}" for n in range(1, 31)]


def test_every_reference_is_a_draft_pending_confirmation(definition: ChecklistDefinition) -> None:
    assert {item.reference_status for item in definition.items} == {ReferenceStatus.DRAFT}


def test_seed_never_uses_forbidden_wording(definition: ChecklistDefinition) -> None:
    for item in definition.items:
        for text in (item.name, item.description, item.evaluation_question, item.expected_evidence):
            assert not FORBIDDEN.search(text), f"{item.code}: {text}"


def test_iso_07_matches_the_reference_format(definition: ChecklistDefinition) -> None:
    item = next(item for item in definition.items if item.code == "ISO-07")
    assert item.name == "Gestión de activos"
    assert "inventario" in item.keywords


def _raw() -> dict[str, object]:
    raw = yaml.safe_load(SEED.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    return raw


def test_duplicate_codes_are_rejected() -> None:
    raw = _raw()
    items = raw["items"]
    assert isinstance(items, list)
    raw["items"] = [*items, items[0]]
    with pytest.raises(ValidationError, match="unique"):
        ChecklistDefinition.model_validate(raw)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("code", "CIS-1", "ISO-01"),
        ("cis_reference", "CIS-1", "never CIS-1"),
        ("keywords", [], "at least 1"),
        ("priority", "URGENT", "priority"),
    ],
)
def test_invalid_items_are_rejected(field: str, value: object, message: str) -> None:
    raw = _raw()
    items = raw["items"]
    assert isinstance(items, list)
    first = dict(items[0])
    first[field] = value
    raw["items"] = [first]
    with pytest.raises(ValidationError, match=message):
        ChecklistDefinition.model_validate(raw)
