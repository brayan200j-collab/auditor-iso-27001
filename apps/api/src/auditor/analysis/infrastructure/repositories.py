from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.analysis.application.ports import LlmCallRecord
from auditor.analysis.domain.evidence import Citation
from auditor.analysis.domain.finding import AIFindingRecord, FindingDraft, Outcome
from auditor.analysis.infrastructure.models import AIFindingModel, LlmCallModel
from auditor.shared.domain.vocabulary import FindingStatus, Level, Priority

SessionFactory = Callable[[], AsyncSession]


def _citation_json(citation: Citation) -> dict[str, Any]:
    return {
        "document_id": str(citation.document_id),
        "chunk_id": str(citation.chunk_id),
        "page": citation.page,
        "quote": citation.quote,
        "citation_verified": citation.citation_verified,
    }


def _citation(data: dict[str, Any]) -> Citation:
    return Citation(
        document_id=UUID(data["document_id"]),
        chunk_id=UUID(data["chunk_id"]),
        page=int(data["page"]),
        quote=str(data["quote"]),
        citation_verified=bool(data["citation_verified"]),
    )


def to_record(model: AIFindingModel) -> AIFindingRecord:
    return AIFindingRecord(
        id=model.id,
        created_at=model.created_at,
        evaluation_id=model.evaluation_id,
        analysis_run_id=model.analysis_run_id,
        checklist_item_id=model.checklist_item_id,
        criterion_code=model.criterion_code,
        outcome=Outcome(model.outcome),
        status=FindingStatus(model.status) if model.status else None,
        confidence=Decimal(model.confidence) if model.confidence is not None else None,
        evidence=tuple(_citation(item) for item in model.evidence),
        gap=model.gap,
        recommendation=model.recommendation,
        preliminary_priority=(
            Priority(model.preliminary_priority) if model.preliminary_priority else None
        ),
        estimated_effort=Level(model.estimated_effort) if model.estimated_effort else None,
        risk_level=Level(model.risk_level) if model.risk_level else None,
        llm_called=model.llm_called,
        error_summary=model.error_summary,
        provider=model.provider,
        model=model.model,
        prompt_version=model.prompt_version,
    )


class SqlFindingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, finding: FindingDraft) -> AIFindingRecord:
        model = AIFindingModel(
            evaluation_id=finding.evaluation_id,
            analysis_run_id=finding.analysis_run_id,
            checklist_item_id=finding.checklist_item_id,
            criterion_code=finding.criterion_code,
            outcome=finding.outcome,
            status=finding.status,
            confidence=finding.confidence,
            evidence=[_citation_json(citation) for citation in finding.evidence],
            gap=finding.gap,
            recommendation=finding.recommendation,
            preliminary_priority=finding.preliminary_priority,
            estimated_effort=finding.estimated_effort,
            risk_level=finding.risk_level,
            requires_human_review=finding.requires_human_review,
            has_unverified_citations=finding.has_unverified_citations,
            llm_called=finding.llm_called,
            error_summary=finding.error_summary,
            provider=finding.provider,
            model=finding.model,
            prompt_version=finding.prompt_version,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return to_record(model)

    async def evaluated_item_ids(self, analysis_run_id: UUID) -> set[UUID]:
        rows = await self._session.scalars(
            select(AIFindingModel.checklist_item_id).where(
                AIFindingModel.analysis_run_id == analysis_run_id
            )
        )
        return set(rows.all())

    async def list_for_run(self, analysis_run_id: UUID) -> list[AIFindingRecord]:
        models = await self._session.scalars(
            select(AIFindingModel)
            .where(AIFindingModel.analysis_run_id == analysis_run_id)
            .order_by(AIFindingModel.criterion_code)
        )
        return [to_record(model) for model in models]


class SqlLlmCallRecorder:
    """Usage is recorded in its own transaction so it survives a failed analysis."""

    def __init__(self, session: AsyncSession, session_factory: SessionFactory) -> None:
        self._session = session
        self._session_factory = session_factory

    async def record(self, call: LlmCallRecord) -> None:
        async with self._session_factory() as session:
            session.add(
                LlmCallModel(
                    evaluation_id=call.evaluation_id,
                    analysis_run_id=call.analysis_run_id,
                    criterion_code=call.criterion_code,
                    provider=call.provider,
                    model=call.model,
                    prompt_version=call.prompt_version,
                    attempt=call.attempt,
                    input_tokens=call.input_tokens,
                    output_tokens=call.output_tokens,
                    duration_ms=call.duration_ms,
                    estimated_cost_usd=call.estimated_cost_usd,
                    outcome=call.outcome,
                    error_summary=call.error_summary,
                    structured_result=call.structured_result,
                )
            )
            await session.commit()

    async def count_for_evaluation(self, evaluation_id: UUID) -> int:
        async with self._session_factory() as session:
            count = await session.scalar(
                select(func.count()).where(LlmCallModel.evaluation_id == evaluation_id)
            )
        return count or 0
