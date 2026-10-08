from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.feedback.domain.feedback import Feedback
from auditor.feedback.infrastructure.models import FeedbackModel


class SqlFeedbackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def submitted_at(self, evaluation_id: UUID) -> datetime | None:
        return await self._session.scalar(
            select(FeedbackModel.created_at).where(FeedbackModel.evaluation_id == evaluation_id)
        )

    async def add(self, feedback: Feedback) -> None:
        answers = feedback.answers
        self._session.add(
            FeedbackModel(
                id=feedback.id,
                evaluation_id=feedback.evaluation_id,
                company_id=feedback.company_id,
                user_id=feedback.user_id,
                usefulness=answers.usefulness,
                ease_of_use=answers.ease_of_use,
                trust_in_results=answers.trust_in_results,
                actionable_recommendations=answers.actionable_recommendations,
                manual_time_hours=answers.manual_time_hours,
                system_time_hours=answers.system_time_hours,
                willingness_to_use=answers.willingness_to_use,
                willingness_to_pay=answers.willingness_to_pay.value,
                comments=answers.comments,
            )
        )
        await self._session.flush()
