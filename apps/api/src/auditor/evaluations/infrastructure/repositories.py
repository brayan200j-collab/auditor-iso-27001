from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, exists, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.evaluations.application.ports import EvaluationFilters, NewEvaluation
from auditor.evaluations.domain.evaluation import AnalysisRun, Evaluation, FailureReason
from auditor.evaluations.domain.scope import (
    AllEvaluations,
    AssignedEvaluations,
    CompanyEvaluations,
    DataScope,
)
from auditor.evaluations.domain.status import EvaluationStatus
from auditor.evaluations.infrastructure.models import (
    AnalysisRunModel,
    ConsentModel,
    EvaluationModel,
)
from auditor.shared.domain.errors import ConflictError, ResourceNotFoundError
from auditor.shared.domain.pagination import Page, PageRequest


def _to_evaluation(model: EvaluationModel) -> Evaluation:
    return Evaluation(
        id=model.id,
        company_id=model.company_id,
        created_by=model.created_by,
        reviewer_id=model.reviewer_id,
        title=model.title,
        status=EvaluationStatus(model.status),
        current_run_number=model.current_run_number,
        rejection_reason=model.rejection_reason,
        failure_reason=FailureReason(model.failure_reason) if model.failure_reason else None,
        failed_stage=EvaluationStatus(model.failed_stage) if model.failed_stage else None,
        submitted_at=model.submitted_at,
        approved_at=model.approved_at,
        approved_by=model.approved_by,
        rejected_at=model.rejected_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_run(model: AnalysisRunModel) -> AnalysisRun:
    return AnalysisRun(
        id=model.id,
        evaluation_id=model.evaluation_id,
        run_number=model.run_number,
        checklist_version_id=model.checklist_version_id,
        started_at=model.started_at,
        finished_at=model.finished_at,
    )


def scoped(query: Select[EvaluationModel], scope: DataScope) -> Select[EvaluationModel]:
    """Applies the mandatory data scope. Every evaluation query goes through here."""
    match scope:
        case AllEvaluations():
            return query
        case CompanyEvaluations(company_id=company_id):
            return query.where(EvaluationModel.company_id == company_id)
        case AssignedEvaluations(reviewer_id=reviewer_id):
            return query.where(EvaluationModel.reviewer_id == reviewer_id)


class SqlEvaluationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, evaluation: NewEvaluation) -> Evaluation:
        model = EvaluationModel(
            company_id=evaluation.company_id,
            created_by=evaluation.created_by,
            title=evaluation.title,
            status=EvaluationStatus.DRAFT,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_evaluation(model)

    async def get(self, evaluation_id: UUID, scope: DataScope) -> Evaluation | None:
        query = scoped(select(EvaluationModel).where(EvaluationModel.id == evaluation_id), scope)
        model = await self._session.scalar(query)
        return _to_evaluation(model) if model else None

    async def exists(self, evaluation_id: UUID) -> bool:
        return bool(
            await self._session.scalar(select(exists().where(EvaluationModel.id == evaluation_id)))
        )

    async def list(
        self, scope: DataScope, filters: EvaluationFilters, page: PageRequest
    ) -> Page[Evaluation]:
        query = scoped(select(EvaluationModel), scope)
        if filters.status:
            query = query.where(EvaluationModel.status == filters.status)
        if filters.company_id:
            query = query.where(EvaluationModel.company_id == filters.company_id)
        total = await self._session.scalar(select(func.count()).select_from(query.subquery()))
        models = await self._session.scalars(
            query.order_by(EvaluationModel.created_at.desc())
            .offset(page.offset)
            .limit(page.page_size)
        )
        return Page(
            items=[_to_evaluation(model) for model in models],
            total=total or 0,
            page=page.page,
            page_size=page.page_size,
        )

    async def count_for_company(self, company_id: UUID) -> int:
        count = await self._session.scalar(
            select(func.count()).where(EvaluationModel.company_id == company_id)
        )
        return count or 0

    async def save(self, evaluation: Evaluation, expected_status: EvaluationStatus) -> None:
        result = await self._session.execute(
            update(EvaluationModel)
            .where(EvaluationModel.id == evaluation.id, EvaluationModel.status == expected_status)
            .values(
                status=evaluation.status,
                current_run_number=evaluation.current_run_number,
                rejection_reason=evaluation.rejection_reason,
                failure_reason=evaluation.failure_reason,
                failed_stage=evaluation.failed_stage,
                submitted_at=evaluation.submitted_at,
                approved_at=evaluation.approved_at,
                approved_by=evaluation.approved_by,
                rejected_at=evaluation.rejected_at,
                updated_at=evaluation.updated_at,
            )
            .returning(EvaluationModel.id)
        )
        if result.scalar_one_or_none() is None:
            raise ConflictError(
                "La evaluación cambió mientras se procesaba tu solicitud. Actualiza la página.",
                detail=f"expected status {expected_status}",
            )

    async def set_reviewer(self, evaluation_id: UUID, reviewer_id: UUID) -> None:
        await self._session.execute(
            update(EvaluationModel)
            .where(EvaluationModel.id == evaluation_id)
            .values(reviewer_id=reviewer_id, updated_at=datetime.now(UTC))
        )

    async def lock(self, evaluation_id: UUID) -> None:
        await self._session.execute(
            select(EvaluationModel.id).where(EvaluationModel.id == evaluation_id).with_for_update()
        )


class SqlAnalysisRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, evaluation_id: UUID, run_number: int) -> AnalysisRun:
        model = AnalysisRunModel(evaluation_id=evaluation_id, run_number=run_number)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_run(model)

    async def current(self, evaluation: Evaluation) -> AnalysisRun:
        model = await self._session.scalar(
            select(AnalysisRunModel).where(
                AnalysisRunModel.evaluation_id == evaluation.id,
                AnalysisRunModel.run_number == evaluation.current_run_number,
            )
        )
        if model is None:
            raise ResourceNotFoundError(detail="analysis run missing")
        return _to_run(model)

    async def get(self, run_id: UUID) -> AnalysisRun | None:
        model = await self._session.get(AnalysisRunModel, run_id)
        return _to_run(model) if model else None

    async def bind_checklist(self, run_id: UUID, checklist_version_id: UUID) -> None:
        await self._session.execute(
            update(AnalysisRunModel)
            .where(AnalysisRunModel.id == run_id)
            .values(checklist_version_id=checklist_version_id)
        )

    async def mark_started(self, run_id: UUID) -> None:
        await self._session.execute(
            update(AnalysisRunModel)
            .where(AnalysisRunModel.id == run_id, AnalysisRunModel.started_at.is_(None))
            .values(started_at=datetime.now(UTC))
        )

    async def mark_finished(self, run_id: UUID) -> None:
        await self._session.execute(
            update(AnalysisRunModel)
            .where(AnalysisRunModel.id == run_id)
            .values(finished_at=datetime.now(UTC))
        )


class SqlConsentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def has_consent(self, evaluation_id: UUID, user_id: UUID, version: str) -> bool:
        return bool(
            await self._session.scalar(
                select(
                    exists().where(
                        ConsentModel.evaluation_id == evaluation_id,
                        ConsentModel.user_id == user_id,
                        ConsentModel.text_version == version,
                    )
                )
            )
        )

    async def add(self, evaluation_id: UUID, user_id: UUID, version: str, sha256: str) -> None:
        self._session.add(
            ConsentModel(
                evaluation_id=evaluation_id,
                user_id=user_id,
                text_version=version,
                text_sha256=sha256,
            )
        )
        await self._session.flush()
