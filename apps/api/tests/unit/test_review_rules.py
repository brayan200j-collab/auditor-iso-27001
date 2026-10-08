from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from auditor.analysis.domain.evidence import Citation
from auditor.analysis.domain.finding import AIFindingRecord, Outcome
from auditor.review.application.values import ai_values, verified_evidence
from auditor.review.domain.review import FinalEvidence, FinalValues, approve, discard, edit
from auditor.shared.domain.errors import ValidationFailedError
from auditor.shared.domain.vocabulary import FindingStatus, Level, Priority, ReviewStatus

VALUES = FinalValues(
    FindingStatus.PARTIAL, "Brecha", "Recomendación", Priority.HIGH, Level.LOW, Level.HIGH
)
EVIDENCE = (FinalEvidence(uuid4(), 3, "El inventario se actualiza cada semestre"),)


def test_approve_keeps_ai_values() -> None:
    decision = approve(VALUES, EVIDENCE, "  De acuerdo  ")
    assert decision.review_status is ReviewStatus.APPROVED
    assert decision.values == VALUES
    assert decision.comment == "De acuerdo"


def test_unclassified_findings_cannot_be_approved_as_is() -> None:
    unclassified = FinalValues(None, "", "", None, None, None)
    with pytest.raises(ValidationFailedError, match="Edítalo o descártalo"):
        approve(unclassified, (), None)


def test_edit_requires_a_complete_classification() -> None:
    with pytest.raises(ValidationFailedError):
        edit(
            FinalValues(FindingStatus.FOUND, " ", "r", Priority.LOW, Level.LOW, Level.LOW), (), None
        )
    with pytest.raises(ValidationFailedError):
        edit(FinalValues(FindingStatus.FOUND, "g", "r", None, Level.LOW, Level.LOW), (), None)


def test_editing_to_no_evidence_drops_citations() -> None:
    no_evidence = FinalValues(
        FindingStatus.NO_DOCUMENTARY_EVIDENCE, "g", "r", Priority.HIGH, Level.LOW, Level.HIGH
    )
    decision = edit(no_evidence, EVIDENCE, None)
    assert decision.review_status is ReviewStatus.EDITED_APPROVED
    assert decision.evidence == ()


@pytest.mark.parametrize("comment", [None, "", "corto"])
def test_discard_requires_a_reason(comment: str | None) -> None:
    with pytest.raises(ValidationFailedError, match="motivo"):
        discard(VALUES, comment)


def test_only_verified_citations_can_reach_the_company() -> None:
    document = uuid4()
    finding = AIFindingRecord(
        id=uuid4(),
        created_at=datetime.now(UTC),
        evaluation_id=uuid4(),
        analysis_run_id=uuid4(),
        checklist_item_id=uuid4(),
        criterion_code="ISO-07",
        outcome=Outcome.OK,
        status=FindingStatus.FOUND,
        confidence=Decimal("0.9"),
        evidence=(
            Citation(document, uuid4(), 3, "cita real del documento", True),
            Citation(document, uuid4(), 4, "cita inventada por el modelo", False),
        ),
        gap="g",
        recommendation="r",
        preliminary_priority=Priority.LOW,
        estimated_effort=Level.LOW,
        risk_level=Level.LOW,
        llm_called=True,
        error_summary=None,
        provider="fake",
        model="m",
        prompt_version="v1",
    )
    assert [item.quote for item in verified_evidence(finding)] == ["cita real del documento"]
    assert ai_values(finding).priority is Priority.LOW
