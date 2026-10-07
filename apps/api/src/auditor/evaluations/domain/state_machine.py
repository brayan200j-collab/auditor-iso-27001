"""Evaluation lifecycle (CLAUDE.md section 11) as an explicit transition table.

Each row answers: from which state, by which trigger, who may fire it, and the resulting state.
Effects (timestamps, reasons, new analysis runs, jobs) are applied by `Evaluation.apply` and the
use cases; every transition is audited by the caller. Anything not listed raises
`InvalidStateTransitionError`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from auditor.evaluations.domain.status import EvaluationStatus as S
from auditor.shared.domain.errors import InvalidStateTransitionError


class Trigger(StrEnum):
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    LAST_DOCUMENT_DELETED = "LAST_DOCUMENT_DELETED"
    START_ANALYSIS = "START_ANALYSIS"
    EXTRACTION_COMPLETED = "EXTRACTION_COMPLETED"
    ANALYSIS_COMPLETED = "ANALYSIS_COMPLETED"
    PROCESSING_FAILED = "PROCESSING_FAILED"
    RETRY_EXTRACTION = "RETRY_EXTRACTION"
    RETRY_ANALYSIS = "RETRY_ANALYSIS"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    NEW_DOCUMENT_AFTER_REJECTION = "NEW_DOCUMENT_AFTER_REJECTION"


class Party(StrEnum):
    """Who fires a transition. Concrete permissions are still checked by the use case."""

    SME = "SME"
    REVIEWER = "REVIEWER"
    SYSTEM = "SYSTEM"


@dataclass(frozen=True, slots=True)
class Transition:
    source: S
    trigger: Trigger
    parties: frozenset[Party]
    target: S


_SME = frozenset({Party.SME})
_REVIEW = frozenset({Party.REVIEWER})
_SYSTEM = frozenset({Party.SYSTEM})

TRANSITIONS: tuple[Transition, ...] = (
    Transition(S.DRAFT, Trigger.DOCUMENT_UPLOADED, _SME, S.RECEIVED),
    Transition(S.RECEIVED, Trigger.DOCUMENT_UPLOADED, _SME, S.RECEIVED),
    Transition(S.RECEIVED, Trigger.LAST_DOCUMENT_DELETED, _SME, S.DRAFT),
    Transition(S.RECEIVED, Trigger.START_ANALYSIS, _SME, S.EXTRACTING),
    Transition(S.EXTRACTING, Trigger.EXTRACTION_COMPLETED, _SYSTEM, S.ANALYZING),
    Transition(S.ANALYZING, Trigger.ANALYSIS_COMPLETED, _SYSTEM, S.PENDING_REVIEW),
    Transition(S.EXTRACTING, Trigger.PROCESSING_FAILED, _SYSTEM, S.FAILED),
    Transition(S.ANALYZING, Trigger.PROCESSING_FAILED, _SYSTEM, S.FAILED),
    Transition(S.FAILED, Trigger.RETRY_EXTRACTION, _REVIEW, S.EXTRACTING),
    Transition(S.FAILED, Trigger.RETRY_ANALYSIS, _REVIEW, S.ANALYZING),
    Transition(S.PENDING_REVIEW, Trigger.APPROVE, _REVIEW, S.APPROVED),
    Transition(S.PENDING_REVIEW, Trigger.REJECT, _REVIEW, S.REJECTED),
    Transition(S.REJECTED, Trigger.NEW_DOCUMENT_AFTER_REJECTION, _SME, S.RECEIVED),
)

_INDEX = {(row.source, row.trigger): row for row in TRANSITIONS}


def resolve(source: S, trigger: Trigger, party: Party) -> S:
    """Returns the target state or raises InvalidStateTransitionError."""
    row = _INDEX.get((source, trigger))
    if row is None or party not in row.parties:
        raise InvalidStateTransitionError(detail=f"{source} --{trigger}/{party}--> ?")
    return row.target


def allowed_triggers(source: S, party: Party) -> set[Trigger]:
    return {row.trigger for row in TRANSITIONS if row.source is source and party in row.parties}
