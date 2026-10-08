from __future__ import annotations

from auditor.analysis.public import AIFindingRecord
from auditor.review.domain.review import FinalEvidence, FinalValues


def ai_values(finding: AIFindingRecord) -> FinalValues:
    return FinalValues(
        status=finding.status,
        gap=finding.gap,
        recommendation=finding.recommendation,
        priority=finding.preliminary_priority,
        effort=finding.estimated_effort,
        risk_level=finding.risk_level,
    )


def verified_evidence(finding: AIFindingRecord) -> tuple[FinalEvidence, ...]:
    """Only citations verified against the real fragment can ever reach the company."""
    return tuple(
        FinalEvidence(document_id=c.document_id, page=c.page, quote=c.quote)
        for c in finding.evidence
        if c.citation_verified
    )
