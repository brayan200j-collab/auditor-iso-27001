from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from auditor.evaluations.public import EvaluationAccess, EvaluationStatus
from auditor.feedback.application.ports import FeedbackRepository
from auditor.feedback.domain.feedback import Feedback, SurveyAnswers
from auditor.identity.public import Permission
from auditor.shared.application.ports import AuditLogger, UnitOfWork
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.audit import AuditAction, AuditEntry
from auditor.shared.domain.errors import ConflictError


class SurveyNotAvailableError(ConflictError):
    default_message = "La encuesta se habilita cuando la evaluación está aprobada."


class SurveyAlreadyAnsweredError(ConflictError):
    default_message = "Esta evaluación ya tiene una respuesta a la encuesta. ¡Gracias!"


@dataclass(frozen=True, slots=True)
class SurveyStatus:
    available: bool
    submitted_at: datetime | None


class SubmitFeedback:
    def __init__(
        self,
        access: EvaluationAccess,
        feedback: FeedbackRepository,
        audit: AuditLogger,
        uow: UnitOfWork,
    ) -> None:
        self._access = access
        self._feedback = feedback
        self._audit = audit
        self._uow = uow

    async def execute(self, actor: Actor, evaluation_id: UUID, answers: SurveyAnswers) -> None:
        evaluation = await self._access.require(actor, evaluation_id, Permission.SUBMIT_FEEDBACK)
        if evaluation.status is not EvaluationStatus.APPROVED:
            raise SurveyNotAvailableError()
        if await self._feedback.submitted_at(evaluation.id):
            raise SurveyAlreadyAnsweredError()
        await self._feedback.add(
            Feedback(
                id=uuid4(),
                evaluation_id=evaluation.id,
                company_id=evaluation.company_id,
                user_id=actor.user_id,
                answers=answers.validated(),
            )
        )
        await self._audit.record(
            AuditEntry(
                action=AuditAction.FEEDBACK_SUBMITTED,
                actor_id=actor.user_id,
                actor_role=actor.role.value,
                company_id=evaluation.company_id,
                resource_type="evaluation",
                resource_id=evaluation.id,
            )
        )
        await self._uow.commit()


class GetSurveyStatus:
    def __init__(self, access: EvaluationAccess, feedback: FeedbackRepository) -> None:
        self._access = access
        self._feedback = feedback

    async def execute(self, actor: Actor, evaluation_id: UUID) -> SurveyStatus:
        evaluation = await self._access.require(
            actor, evaluation_id, Permission.VIEW_APPROVED_RESULTS
        )
        return SurveyStatus(
            available=evaluation.status is EvaluationStatus.APPROVED,
            submitted_at=await self._feedback.submitted_at(evaluation.id),
        )
