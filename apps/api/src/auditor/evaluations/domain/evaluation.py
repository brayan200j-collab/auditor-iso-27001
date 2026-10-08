from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from auditor.evaluations.domain.state_machine import Party, Trigger, resolve
from auditor.evaluations.domain.status import EvaluationStatus
from auditor.shared.domain.errors import ValidationFailedError

TITLE_MIN = 3
TITLE_MAX = 200
REASON_MIN = 10
REASON_MAX = 2000


class FailureReason(StrEnum):
    """User-facing causes of a failed run (the technical detail stays in logs and jobs)."""

    EXTRACTION_ERROR = "EXTRACTION_ERROR"
    ANALYSIS_ERROR = "ANALYSIS_ERROR"
    INTERRUPTED = "INTERRUPTED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"


@dataclass(frozen=True, slots=True)
class Evaluation:
    id: UUID
    company_id: UUID
    created_by: UUID
    reviewer_id: UUID | None
    title: str
    status: EvaluationStatus
    current_run_number: int
    rejection_reason: str | None
    failure_reason: FailureReason | None
    failed_stage: EvaluationStatus | None
    submitted_at: datetime | None
    approved_at: datetime | None
    approved_by: UUID | None
    rejected_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @property
    def is_locked(self) -> bool:
        """APPROVED is immutable: later changes require a new evaluation."""
        return self.status is EvaluationStatus.APPROVED

    def apply(
        self,
        trigger: Trigger,
        party: Party,
        now: datetime,
        *,
        actor_id: UUID | None = None,
        reason: str | None = None,
        failure: FailureReason | None = None,
    ) -> Evaluation:
        target = resolve(self.status, trigger, party)
        changes: dict[str, object] = {"status": target, "updated_at": now}
        if trigger is Trigger.START_ANALYSIS:
            changes["submitted_at"] = now
        elif trigger is Trigger.PROCESSING_FAILED:
            changes["failure_reason"] = failure or FailureReason.ANALYSIS_ERROR
            changes["failed_stage"] = self.status
        elif trigger in {Trigger.RETRY_EXTRACTION, Trigger.RETRY_ANALYSIS}:
            changes["failure_reason"] = None
            changes["failed_stage"] = None
        elif trigger is Trigger.APPROVE:
            changes["approved_at"] = now
            changes["approved_by"] = actor_id
        elif trigger is Trigger.REJECT:
            changes["rejection_reason"] = validate_reason(reason)
            changes["rejected_at"] = now
        elif trigger is Trigger.NEW_DOCUMENT_AFTER_REJECTION:
            changes["current_run_number"] = self.current_run_number + 1
            changes["submitted_at"] = None
        return replace(self, **changes)  # type: ignore[arg-type]


def validate_title(value: str) -> str:
    title = " ".join(value.split())
    if not TITLE_MIN <= len(title) <= TITLE_MAX:
        raise ValidationFailedError(
            "El nombre de la evaluación debe tener entre 3 y 200 caracteres."
        )
    return title


def validate_reason(value: str | None) -> str:
    reason = " ".join((value or "").split())
    if not REASON_MIN <= len(reason) <= REASON_MAX:
        raise ValidationFailedError(
            "El motivo del rechazo es obligatorio (entre 10 y 2000 caracteres)."
        )
    return reason


@dataclass(frozen=True, slots=True)
class AnalysisRun:
    id: UUID
    evaluation_id: UUID
    run_number: int
    checklist_version_id: UUID | None
    started_at: datetime | None
    finished_at: datetime | None
