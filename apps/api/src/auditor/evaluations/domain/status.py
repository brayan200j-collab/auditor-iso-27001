from __future__ import annotations

from enum import StrEnum


class EvaluationStatus(StrEnum):
    DRAFT = "DRAFT"
    RECEIVED = "RECEIVED"
    EXTRACTING = "EXTRACTING"
    ANALYZING = "ANALYZING"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


PROCESSING_STATUSES = frozenset({EvaluationStatus.EXTRACTING, EvaluationStatus.ANALYZING})
