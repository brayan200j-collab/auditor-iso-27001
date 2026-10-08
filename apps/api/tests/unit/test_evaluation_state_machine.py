from __future__ import annotations

import itertools
from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st

from auditor.evaluations.domain.evaluation import (
    Evaluation,
    FailureReason,
    validate_reason,
    validate_title,
)
from auditor.evaluations.domain.progress import StepState, progress
from auditor.evaluations.domain.state_machine import (
    TRANSITIONS,
    Party,
    Trigger,
    allowed_triggers,
    resolve,
)
from auditor.evaluations.domain.status import EvaluationStatus as S
from auditor.shared.domain.errors import InvalidStateTransitionError, ValidationFailedError

NOW = datetime(2026, 10, 7, tzinfo=UTC)
TABLE = {
    (row.source, row.trigger, party): row.target for row in TRANSITIONS for party in row.parties
}


def make(status: S = S.DRAFT) -> Evaluation:
    return Evaluation(
        id=uuid4(),
        company_id=uuid4(),
        created_by=uuid4(),
        reviewer_id=None,
        title="Evaluación sintética",
        status=status,
        current_run_number=1,
        rejection_reason=None,
        failure_reason=None,
        failed_stage=None,
        submitted_at=None,
        approved_at=None,
        approved_by=None,
        rejected_at=None,
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.mark.parametrize(("source", "trigger", "party"), list(itertools.product(S, Trigger, Party)))
def test_only_listed_transitions_are_allowed(source: S, trigger: Trigger, party: Party) -> None:
    expected = TABLE.get((source, trigger, party))
    if expected is None:
        with pytest.raises(InvalidStateTransitionError):
            resolve(source, trigger, party)
    else:
        assert resolve(source, trigger, party) is expected


def test_approved_is_terminal_and_only_humans_decide() -> None:
    for party in Party:
        assert allowed_triggers(S.APPROVED, party) == set()
    assert allowed_triggers(S.PENDING_REVIEW, Party.SYSTEM) == set()
    assert allowed_triggers(S.PENDING_REVIEW, Party.SME) == set()
    assert allowed_triggers(S.PENDING_REVIEW, Party.REVIEWER) == {Trigger.APPROVE, Trigger.REJECT}


@given(st.lists(st.tuples(st.sampled_from(Trigger), st.sampled_from(Party)), max_size=30))
def test_random_walks_only_reach_approved_through_human_review(
    steps: list[tuple[Trigger, Party]],
) -> None:
    status = S.DRAFT
    for trigger, party in steps:
        try:
            target = resolve(status, trigger, party)
        except InvalidStateTransitionError:
            continue
        if target is S.APPROVED:
            assert status is S.PENDING_REVIEW
            assert party is Party.REVIEWER
        assert status is not S.APPROVED
        status = target


def test_effects_of_each_transition() -> None:
    received = make().apply(Trigger.DOCUMENT_UPLOADED, Party.SME, NOW)
    extracting = received.apply(Trigger.START_ANALYSIS, Party.SME, NOW)
    assert extracting.submitted_at == NOW

    failed = extracting.apply(
        Trigger.PROCESSING_FAILED, Party.SYSTEM, NOW, failure=FailureReason.EXTRACTION_ERROR
    )
    assert (failed.failure_reason, failed.failed_stage) == (
        FailureReason.EXTRACTION_ERROR,
        S.EXTRACTING,
    )
    retried = failed.apply(Trigger.RETRY_EXTRACTION, Party.REVIEWER, NOW)
    assert retried.failure_reason is None
    assert retried.failed_stage is None

    pending = retried.apply(Trigger.EXTRACTION_COMPLETED, Party.SYSTEM, NOW).apply(
        Trigger.ANALYSIS_COMPLETED, Party.SYSTEM, NOW
    )
    reviewer = uuid4()
    approved = pending.apply(Trigger.APPROVE, Party.REVIEWER, NOW, actor_id=reviewer)
    assert (approved.status, approved.approved_by, approved.is_locked) == (
        S.APPROVED,
        reviewer,
        True,
    )

    rejected = pending.apply(
        Trigger.REJECT, Party.REVIEWER, NOW, reason="Falta la política de copias de respaldo."
    )
    assert rejected.rejection_reason == "Falta la política de copias de respaldo."
    resubmitted = rejected.apply(Trigger.NEW_DOCUMENT_AFTER_REJECTION, Party.SME, NOW)
    assert (resubmitted.status, resubmitted.current_run_number) == (S.RECEIVED, 2)


def test_rejection_requires_a_reason() -> None:
    pending = replace(make(), status=S.PENDING_REVIEW)
    with pytest.raises(ValidationFailedError):
        pending.apply(Trigger.REJECT, Party.REVIEWER, NOW, reason="  ")


def test_text_validation() -> None:
    assert validate_title("  Evaluación   2026 ") == "Evaluación 2026"
    assert validate_reason("Motivo  suficientemente largo") == "Motivo suficientemente largo"
    for invalid in ("ab", "x" * 201):
        with pytest.raises(ValidationFailedError):
            validate_title(invalid)


@pytest.mark.parametrize(
    ("status", "failed_stage", "expected"),
    [
        (S.DRAFT, None, ["PENDING"] * 5),
        (S.RECEIVED, None, ["CURRENT", "PENDING", "PENDING", "PENDING", "PENDING"]),
        (S.ANALYZING, None, ["DONE", "DONE", "CURRENT", "PENDING", "PENDING"]),
        (S.FAILED, S.ANALYZING, ["DONE", "DONE", "FAILED", "PENDING", "PENDING"]),
        (S.FAILED, None, ["DONE", "FAILED", "PENDING", "PENDING", "PENDING"]),
        (S.REJECTED, None, ["DONE", "DONE", "DONE", "FAILED", "PENDING"]),
        (S.APPROVED, None, ["DONE"] * 5),
    ],
)
def test_progress_timeline(status: S, failed_stage: S | None, expected: list[str]) -> None:
    steps = progress(status, failed_stage)
    assert [step.step for step in steps] == [
        S.RECEIVED,
        S.EXTRACTING,
        S.ANALYZING,
        S.PENDING_REVIEW,
        S.APPROVED,
    ]
    assert [step.state for step in steps] == [StepState(value) for value in expected]
