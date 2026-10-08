from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.review.application.ports import FindingKey, HumanReviewEntry, HumanReviewRecord
from auditor.review.domain.review import FinalEvidence, FinalFinding, FinalValues, ReviewDecision
from auditor.review.infrastructure.models import FinalFindingModel, HumanReviewModel
from auditor.shared.domain.vocabulary import FindingStatus, Level, Priority, ReviewStatus


def _evidence_json(evidence: tuple[FinalEvidence, ...]) -> list[dict[str, Any]]:
    return [
        {"document_id": str(item.document_id), "page": item.page, "quote": item.quote}
        for item in evidence
    ]


def _to_final(model: FinalFindingModel) -> FinalFinding:
    return FinalFinding(
        id=model.id,
        ai_finding_id=model.ai_finding_id,
        evaluation_id=model.evaluation_id,
        analysis_run_id=model.analysis_run_id,
        checklist_item_id=model.checklist_item_id,
        criterion_code=model.criterion_code,
        review_status=ReviewStatus(model.review_status),
        values=FinalValues(
            status=FindingStatus(model.status) if model.status else None,
            gap=model.gap,
            recommendation=model.recommendation,
            priority=Priority(model.priority) if model.priority else None,
            effort=Level(model.effort) if model.effort else None,
            risk_level=Level(model.risk_level) if model.risk_level else None,
        ),
        evidence=tuple(
            FinalEvidence(UUID(item["document_id"]), int(item["page"]), str(item["quote"]))
            for item in model.evidence
        ),
        reviewer_comment=model.reviewer_comment,
        reviewed_by=model.reviewed_by,
        reviewed_at=model.reviewed_at,
    )


class SqlFinalFindingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_for_ai_finding(self, ai_finding_id: UUID) -> FinalFinding | None:
        model = await self._session.scalar(
            select(FinalFindingModel).where(FinalFindingModel.ai_finding_id == ai_finding_id)
        )
        return _to_final(model) if model else None

    async def save(
        self, key: FindingKey, decision: ReviewDecision, reviewer_id: UUID, now: datetime
    ) -> FinalFinding:
        values = decision.values
        row: dict[str, Any] = {
            "ai_finding_id": key.ai_finding_id,
            "evaluation_id": key.evaluation_id,
            "analysis_run_id": key.analysis_run_id,
            "checklist_item_id": key.checklist_item_id,
            "criterion_code": key.criterion_code,
            "review_status": decision.review_status.value,
            "status": values.status.value if values.status else None,
            "gap": values.gap,
            "recommendation": values.recommendation,
            "priority": values.priority.value if values.priority else None,
            "effort": values.effort.value if values.effort else None,
            "risk_level": values.risk_level.value if values.risk_level else None,
            "evidence": _evidence_json(decision.evidence),
            "reviewer_comment": decision.comment,
            "reviewed_by": reviewer_id,
            "reviewed_at": now,
        }
        insert_row = insert(FinalFindingModel).values(**row)
        statement = insert_row.on_conflict_do_update(
            index_elements=[FinalFindingModel.ai_finding_id],
            set_={
                column: insert_row.excluded[column] for column in row if column != "ai_finding_id"
            },
        ).returning(FinalFindingModel)
        model = (await self._session.execute(statement)).scalar_one()
        return _to_final(model)

    async def list_for_run(self, analysis_run_id: UUID) -> list[FinalFinding]:
        models = await self._session.scalars(
            select(FinalFindingModel)
            .where(FinalFindingModel.analysis_run_id == analysis_run_id)
            .order_by(FinalFindingModel.criterion_code)
        )
        return [_to_final(model) for model in models]


class SqlHumanReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entry: HumanReviewEntry) -> None:
        self._session.add(
            HumanReviewModel(
                ai_finding_id=entry.ai_finding_id,
                evaluation_id=entry.evaluation_id,
                reviewer_id=entry.reviewer_id,
                action=entry.action,
                comment=entry.comment,
                previous_values=entry.previous_values,
                new_values=entry.new_values,
            )
        )
        await self._session.flush()

    async def history(self, ai_finding_id: UUID) -> list[HumanReviewRecord]:
        models = await self._session.scalars(
            select(HumanReviewModel)
            .where(HumanReviewModel.ai_finding_id == ai_finding_id)
            .order_by(HumanReviewModel.created_at)
        )
        return [
            HumanReviewRecord(
                action=model.action,
                comment=model.comment,
                reviewer_id=model.reviewer_id,
                created_at=model.created_at,
            )
            for model in models
        ]
