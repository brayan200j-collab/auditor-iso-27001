from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from auditor.checklist.application.import_checklist import ImportChecklist
from auditor.checklist.domain.entities import VersionStatus
from auditor.checklist.infrastructure.repository import SqlChecklistRepository
from auditor.checklist.infrastructure.yaml_loader import load_checklist_definition
from auditor.shared.infrastructure.database import SessionUnitOfWork
from tests.unit.test_checklist_definition import SEED


async def test_import_publishes_thirty_items_and_is_idempotent(session: AsyncSession) -> None:
    definition = load_checklist_definition(SEED)
    use_case = ImportChecklist(SqlChecklistRepository(session), SessionUnitOfWork(session))

    first = await use_case.execute(definition)
    second = await use_case.execute(definition)

    assert first.created is True
    assert second.created is False
    assert first.version.status is VersionStatus.PUBLISHED
    assert len(first.version.items) == 30
    assert first.version.items[6].label == "ISO-07 · Gestión de activos"
    latest = await SqlChecklistRepository(session).latest_published()
    assert latest is not None
    assert latest.id == first.version.id
