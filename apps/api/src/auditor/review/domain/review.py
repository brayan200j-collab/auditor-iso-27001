"""Human review rules (CLAUDE.md section 14).

Three layers: the AI finding (never modified) → a human review entry per decision → the final
finding, the only version the company will see. Only verified citations reach the final finding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from auditor.shared.domain.errors import ValidationFailedError
from auditor.shared.domain.vocabulary import FindingStatus, Level, Priority, ReviewStatus

COMMENT_MAX = 2000
TEXT_MAX = 2000
DISCARD_COMMENT_MIN = 10


class ReviewAction(StrEnum):
    APPROVE = "APPROVE"
    EDIT = "EDIT"
    DISCARD = "DISCARD"


@dataclass(frozen=True, slots=True)
class FinalEvidence:
    document_id: UUID
    page: int
    quote: str


@dataclass(frozen=True, slots=True)
class FinalValues:
    status: FindingStatus | None
    gap: str
    recommendation: str
    priority: Priority | None
    effort: Level | None
    risk_level: Level | None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "status": self.status.value if self.status else None,
            "gap": self.gap,
            "recommendation": self.recommendation,
            "priority": self.priority.value if self.priority else None,
            "effort": self.effort.value if self.effort else None,
            "risk_level": self.risk_level.value if self.risk_level else None,
        }


@dataclass(frozen=True, slots=True)
class ReviewDecision:
    action: ReviewAction
    review_status: ReviewStatus
    values: FinalValues
    comment: str | None
    evidence: tuple[FinalEvidence, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class FinalFinding:
    id: UUID
    ai_finding_id: UUID
    evaluation_id: UUID
    analysis_run_id: UUID
    checklist_item_id: UUID
    criterion_code: str
    review_status: ReviewStatus
    values: FinalValues
    evidence: tuple[FinalEvidence, ...]
    reviewer_comment: str | None
    reviewed_by: UUID
    reviewed_at: datetime


def _clean(text: str | None, limit: int = TEXT_MAX) -> str:
    cleaned = (text or "").strip()
    if len(cleaned) > limit:
        raise ValidationFailedError(f"El texto supera el máximo de {limit} caracteres.")
    return cleaned


def approve(
    ai_values: FinalValues, evidence: tuple[FinalEvidence, ...], comment: str | None
) -> ReviewDecision:
    if ai_values.status is None or ai_values.priority is None:
        raise ValidationFailedError(
            "La IA no pudo clasificar este criterio. Edítalo o descártalo para continuar."
        )
    return ReviewDecision(
        action=ReviewAction.APPROVE,
        review_status=ReviewStatus.APPROVED,
        values=ai_values,
        comment=_clean(comment, COMMENT_MAX) or None,
        evidence=evidence,
    )


def edit(
    values: FinalValues, evidence: tuple[FinalEvidence, ...], comment: str | None
) -> ReviewDecision:
    if (
        values.status is None
        or values.priority is None
        or values.effort is None
        or values.risk_level is None
    ):
        raise ValidationFailedError("Completa el estado, la prioridad, el riesgo y el esfuerzo.")
    gap, recommendation = _clean(values.gap), _clean(values.recommendation)
    if not gap or not recommendation:
        raise ValidationFailedError("La brecha y la recomendación son obligatorias.")
    clean_values = FinalValues(
        status=values.status,
        gap=gap,
        recommendation=recommendation,
        priority=values.priority,
        effort=values.effort,
        risk_level=values.risk_level,
    )
    evidence_kept = () if values.status is FindingStatus.NO_DOCUMENTARY_EVIDENCE else evidence
    return ReviewDecision(
        action=ReviewAction.EDIT,
        review_status=ReviewStatus.EDITED_APPROVED,
        values=clean_values,
        comment=_clean(comment, COMMENT_MAX) or None,
        evidence=evidence_kept,
    )


def discard(ai_values: FinalValues, comment: str | None) -> ReviewDecision:
    reason = _clean(comment, COMMENT_MAX)
    if len(reason) < DISCARD_COMMENT_MIN:
        raise ValidationFailedError("Indica el motivo del descarte (mínimo 10 caracteres).")
    return ReviewDecision(
        action=ReviewAction.DISCARD,
        review_status=ReviewStatus.DISCARDED,
        values=ai_values,
        comment=reason,
    )
