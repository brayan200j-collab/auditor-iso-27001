from __future__ import annotations

from auditor.checklist.application.definitions import ChecklistDefinition, ChecklistItemDefinition
from auditor.checklist.domain.entities import ChecklistItem, ChecklistVersion


def item_definition(item: ChecklistItem) -> ChecklistItemDefinition:
    return ChecklistItemDefinition(
        code=item.code,
        name=item.name,
        description=item.description,
        evaluation_question=item.evaluation_question,
        expected_evidence=item.expected_evidence,
        iso_reference=item.iso_reference or "",
        cis_reference=item.cis_reference or "",
        nist_reference=item.nist_reference or "",
        reference_status=item.reference_status,
        keywords=list(item.keywords),
        priority=item.priority,
        risk_level=item.risk_level,
        effort=item.effort,
        active=item.active,
    )


def copy_as(version: ChecklistVersion, number: int) -> ChecklistDefinition:
    """Definition of a new version that starts as an exact copy of `version`."""
    return ChecklistDefinition(
        version=number,
        label=f"Checklist propio v{number}",
        items=[item_definition(item) for item in version.items],
    )
