from __future__ import annotations

from typing import Protocol
from uuid import UUID

from auditor.checklist.application.definitions import ChecklistDefinition, ChecklistItemDefinition
from auditor.checklist.domain.entities import ChecklistVersion


class ChecklistRepository(Protocol):
    async def get_by_number(self, version: int) -> ChecklistVersion | None: ...

    async def get(self, version_id: UUID) -> ChecklistVersion | None: ...

    async def latest_published(self) -> ChecklistVersion | None: ...

    async def list_versions(self) -> list[ChecklistVersion]: ...

    async def next_version_number(self) -> int: ...

    async def create_draft(
        self, definition: ChecklistDefinition, created_by: UUID | None
    ) -> ChecklistVersion: ...

    async def replace_draft_items(
        self, version_id: UUID, definition: ChecklistDefinition
    ) -> ChecklistVersion: ...

    async def publish(self, version_id: UUID) -> ChecklistVersion: ...

    async def draft(self) -> ChecklistVersion | None:
        """The single draft version, if any."""
        ...

    async def update_item(
        self, version_id: UUID, definition: ChecklistItemDefinition
    ) -> ChecklistVersion: ...
