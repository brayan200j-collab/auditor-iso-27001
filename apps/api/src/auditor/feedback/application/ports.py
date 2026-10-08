from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from auditor.feedback.domain.feedback import Feedback


class FeedbackRepository(Protocol):
    async def submitted_at(self, evaluation_id: UUID) -> datetime | None: ...

    async def add(self, feedback: Feedback) -> None: ...
