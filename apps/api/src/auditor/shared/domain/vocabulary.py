"""Value vocabularies shared by several modules (checklist, analysis, review, reports)."""

from __future__ import annotations

from enum import StrEnum


class Priority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Level(StrEnum):
    """Used for risk level and estimated effort."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class FindingStatus(StrEnum):
    FOUND = "FOUND"
    PARTIAL = "PARTIAL"
    NO_DOCUMENTARY_EVIDENCE = "NO_DOCUMENTARY_EVIDENCE"


class ReviewStatus(StrEnum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    EDITED_APPROVED = "EDITED_APPROVED"
    DISCARDED = "DISCARDED"


class JobKind(StrEnum):
    EXTRACTION = "EXTRACTION"
    ANALYSIS = "ANALYSIS"
    REPORT = "REPORT"


class JobStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


PRIORITY_RANK = {
    Priority.CRITICAL: 0,
    Priority.HIGH: 1,
    Priority.MEDIUM: 2,
    Priority.LOW: 3,
}
LEVEL_RANK = {Level.HIGH: 0, Level.MEDIUM: 1, Level.LOW: 2}
