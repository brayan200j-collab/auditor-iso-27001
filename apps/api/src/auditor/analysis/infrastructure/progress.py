from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.analysis.infrastructure.models import AIFindingModel
from auditor.checklist.public import ChecklistRepository
from auditor.evaluations.public import AnalysisRun


class FindingProgressReader:
    def __init__(self, session: AsyncSession, checklists: ChecklistRepository) -> None:
        self._session = session
        self._checklists = checklists

    async def progress(self, run: AnalysisRun) -> tuple[int, int] | None:
        if run.checklist_version_id is None:
            return None
        version = await self._checklists.get(run.checklist_version_id)
        if version is None:
            return None
        done = await self._session.scalar(
            select(func.count()).where(AIFindingModel.analysis_run_id == run.id)
        )
        return done or 0, len(version.active_items)
