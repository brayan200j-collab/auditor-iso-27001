from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import Field

from auditor.evaluations.public import Evaluation, EvaluationStatus
from auditor.review.application.approve_evaluation import ApproveEvaluation
from auditor.review.application.get_finding import GetFinding
from auditor.review.application.get_review import GetReview, ReviewItem, ReviewSummary
from auditor.review.application.list_review_queue import ListReviewQueue
from auditor.review.application.reject_evaluation import RejectEvaluation
from auditor.review.application.review_finding import ReviewFinding, ReviewRequest
from auditor.review.domain.review import FinalFinding, FinalValues, ReviewAction
from auditor.shared.api.dependencies import CurrentActor, use_case
from auditor.shared.api.pagination import PageParams
from auditor.shared.api.schemas import ERROR_RESPONSES, ApiModel, PageMeta, RequestModel
from auditor.shared.domain.vocabulary import FindingStatus, Level, Priority, ReviewStatus

router = APIRouter(prefix="/api/v1", tags=["review"], responses=ERROR_RESPONSES)


# ------------------------------------------------------------------ responses


class CriterionResponse(ApiModel):
    code: str
    name: str
    evaluation_question: str
    expected_evidence: str
    iso_reference: str | None
    cis_reference: str | None
    nist_reference: str | None
    reference_status: str


class EvidenceResponse(ApiModel):
    document_id: UUID
    document_name: str | None
    page: int
    quote: str
    citation_verified: bool


class AIFindingResponse(ApiModel):
    status: FindingStatus | None
    confidence: float | None
    evidence: list[EvidenceResponse]
    gap: str
    recommendation: str
    preliminary_priority: Priority | None
    estimated_effort: Level | None
    risk_level: Level | None
    llm_called: bool
    error_summary: str | None
    needs_attention: bool
    provider: str
    model: str
    prompt_version: str
    created_at: datetime


class FinalValuesResponse(ApiModel):
    status: FindingStatus | None
    gap: str
    recommendation: str
    priority: Priority | None
    effort: Level | None
    risk_level: Level | None


class ReviewStateResponse(ApiModel):
    review_status: ReviewStatus
    final: FinalValuesResponse | None
    comment: str | None
    reviewed_at: datetime | None


class ReviewItemResponse(ApiModel):
    finding_id: UUID
    criterion: CriterionResponse
    ai: AIFindingResponse
    review: ReviewStateResponse

    @classmethod
    def of(cls, item: ReviewItem, names: dict[UUID, str]) -> ReviewItemResponse:
        ai, criterion, final = item.ai, item.criterion, item.final
        return cls(
            finding_id=ai.id,
            criterion=CriterionResponse(
                code=criterion.code,
                name=criterion.name,
                evaluation_question=criterion.evaluation_question,
                expected_evidence=criterion.expected_evidence,
                iso_reference=criterion.iso_reference,
                cis_reference=criterion.cis_reference,
                nist_reference=criterion.nist_reference,
                reference_status=criterion.reference_status.value,
            ),
            ai=AIFindingResponse(
                status=ai.status,
                confidence=float(ai.confidence) if ai.confidence is not None else None,
                evidence=[
                    EvidenceResponse(
                        document_id=c.document_id,
                        document_name=names.get(c.document_id),
                        page=c.page,
                        quote=c.quote,
                        citation_verified=c.citation_verified,
                    )
                    for c in ai.evidence
                ],
                gap=ai.gap,
                recommendation=ai.recommendation,
                preliminary_priority=ai.preliminary_priority,
                estimated_effort=ai.estimated_effort,
                risk_level=ai.risk_level,
                llm_called=ai.llm_called,
                error_summary=ai.error_summary,
                needs_attention=ai.needs_attention,
                provider=ai.provider,
                model=ai.model,
                prompt_version=ai.prompt_version,
                created_at=ai.created_at,
            ),
            review=ReviewStateResponse(
                review_status=item.review_status,
                final=_values(final.values) if final else None,
                comment=final.reviewer_comment if final else None,
                reviewed_at=final.reviewed_at if final else None,
            ),
        )


def _values(values: FinalValues) -> FinalValuesResponse:
    return FinalValuesResponse(
        status=values.status,
        gap=values.gap,
        recommendation=values.recommendation,
        priority=values.priority,
        effort=values.effort,
        risk_level=values.risk_level,
    )


class ReviewSummaryResponse(ApiModel):
    total: int
    found: int
    partial: int
    no_evidence: int
    errors: int
    reviewed: int
    pending: int
    needs_attention: int

    @classmethod
    def of(cls, summary: ReviewSummary) -> ReviewSummaryResponse:
        return cls(
            total=summary.total,
            found=summary.found,
            partial=summary.partial,
            no_evidence=summary.no_evidence,
            errors=summary.errors,
            reviewed=summary.reviewed,
            pending=summary.pending,
            needs_attention=summary.needs_attention,
        )


class ReviewResponse(ApiModel):
    evaluation_id: UUID
    title: str
    status: EvaluationStatus
    summary: ReviewSummaryResponse
    items: list[ReviewItemResponse]


class QueueItemResponse(ApiModel):
    evaluation_id: UUID
    title: str
    company_name: str | None
    updated_at: datetime
    findings: int
    reviewed: int


class QueuePage(ApiModel):
    items: list[QueueItemResponse]
    meta: PageMeta


class HistoryEntryResponse(ApiModel):
    action: ReviewAction
    comment: str | None
    reviewer_id: UUID
    created_at: datetime


class FindingDetailResponse(ApiModel):
    evaluation_id: UUID
    evaluation_status: EvaluationStatus
    item: ReviewItemResponse
    history: list[HistoryEntryResponse]


class DecisionResponse(ApiModel):
    id: UUID
    status: EvaluationStatus

    @classmethod
    def of(cls, evaluation: Evaluation) -> DecisionResponse:
        return cls(id=evaluation.id, status=evaluation.status)


class FinalFindingResponse(ApiModel):
    finding_id: UUID
    review_status: ReviewStatus
    final: FinalValuesResponse

    @classmethod
    def of(cls, final: FinalFinding) -> FinalFindingResponse:
        return cls(
            finding_id=final.ai_finding_id,
            review_status=final.review_status,
            final=_values(final.values),
        )


# ------------------------------------------------------------------ requests


class CommentRequest(RequestModel):
    comment: str | None = Field(default=None, max_length=2000)


class DiscardRequest(RequestModel):
    comment: str = Field(min_length=10, max_length=2000)


class EditRequest(RequestModel):
    status: FindingStatus
    gap: str = Field(min_length=1, max_length=2000)
    recommendation: str = Field(min_length=1, max_length=2000)
    priority: Priority
    effort: Level
    risk_level: Level
    comment: str | None = Field(default=None, max_length=2000)


class RejectRequest(RequestModel):
    reason: str = Field(min_length=10, max_length=2000)


# ------------------------------------------------------------------ endpoints


@router.get("/reviews", response_model=QueuePage, summary="Evaluaciones pendientes de revisión")
async def review_queue(
    actor: CurrentActor,
    page: PageParams,
    queue: Annotated[ListReviewQueue, Depends(use_case(ListReviewQueue))],
) -> QueuePage:
    result = await queue.execute(actor, page)
    return QueuePage(
        items=[
            QueueItemResponse(
                evaluation_id=entry.summary.evaluation.id,
                title=entry.summary.evaluation.title,
                company_name=entry.summary.company_name,
                updated_at=entry.summary.evaluation.updated_at,
                findings=entry.findings,
                reviewed=entry.reviewed,
            )
            for entry in result.items
        ],
        meta=PageMeta(total=result.total, page=result.page, page_size=result.page_size),
    )


@router.get(
    "/reviews/{evaluation_id}", response_model=ReviewResponse, summary="Hallazgos para revisión"
)
async def get_review(
    actor: CurrentActor,
    evaluation_id: UUID,
    review: Annotated[GetReview, Depends(use_case(GetReview))],
) -> ReviewResponse:
    view = await review.execute(actor, evaluation_id)
    return ReviewResponse(
        evaluation_id=view.evaluation.id,
        title=view.evaluation.title,
        status=view.evaluation.status,
        summary=ReviewSummaryResponse.of(view.summary),
        items=[ReviewItemResponse.of(item, view.document_names) for item in view.items],
    )


@router.get(
    "/findings/{finding_id}", response_model=FindingDetailResponse, summary="Detalle del hallazgo"
)
async def get_finding(
    actor: CurrentActor,
    finding_id: UUID,
    get: Annotated[GetFinding, Depends(use_case(GetFinding))],
) -> FindingDetailResponse:
    detail = await get.execute(actor, finding_id)
    return FindingDetailResponse(
        evaluation_id=detail.evaluation_id,
        evaluation_status=EvaluationStatus(detail.evaluation_status),
        item=ReviewItemResponse.of(detail.item, detail.document_names),
        history=[
            HistoryEntryResponse(
                action=ReviewAction(entry.action),
                comment=entry.comment,
                reviewer_id=entry.reviewer_id,
                created_at=entry.created_at,
            )
            for entry in detail.history
        ],
    )


@router.patch(
    "/findings/{finding_id}", response_model=FinalFindingResponse, summary="Editar y aprobar"
)
async def edit_finding(
    actor: CurrentActor,
    finding_id: UUID,
    body: EditRequest,
    review: Annotated[ReviewFinding, Depends(use_case(ReviewFinding))],
) -> FinalFindingResponse:
    values = FinalValues(
        status=body.status,
        gap=body.gap,
        recommendation=body.recommendation,
        priority=body.priority,
        effort=body.effort,
        risk_level=body.risk_level,
    )
    final = await review.execute(
        actor, finding_id, ReviewRequest(ReviewAction.EDIT, body.comment, values)
    )
    return FinalFindingResponse.of(final)


@router.post(
    "/findings/{finding_id}/approve",
    response_model=FinalFindingResponse,
    summary="Aprobar el hallazgo tal como lo propuso la IA",
)
async def approve_finding(
    actor: CurrentActor,
    finding_id: UUID,
    body: CommentRequest,
    review: Annotated[ReviewFinding, Depends(use_case(ReviewFinding))],
) -> FinalFindingResponse:
    final = await review.execute(
        actor, finding_id, ReviewRequest(ReviewAction.APPROVE, body.comment)
    )
    return FinalFindingResponse.of(final)


@router.post(
    "/findings/{finding_id}/discard",
    response_model=FinalFindingResponse,
    summary="Descartar el hallazgo (con motivo)",
)
async def discard_finding(
    actor: CurrentActor,
    finding_id: UUID,
    body: DiscardRequest,
    review: Annotated[ReviewFinding, Depends(use_case(ReviewFinding))],
) -> FinalFindingResponse:
    final = await review.execute(
        actor, finding_id, ReviewRequest(ReviewAction.DISCARD, body.comment)
    )
    return FinalFindingResponse.of(final)


@router.post(
    "/evaluations/{evaluation_id}/approve",
    response_model=DecisionResponse,
    summary="Aprobar la evaluación (todos los hallazgos revisados)",
)
async def approve_evaluation(
    actor: CurrentActor,
    evaluation_id: UUID,
    approve: Annotated[ApproveEvaluation, Depends(use_case(ApproveEvaluation))],
) -> DecisionResponse:
    return DecisionResponse.of(await approve.execute(actor, evaluation_id))


@router.post(
    "/evaluations/{evaluation_id}/reject",
    response_model=DecisionResponse,
    summary="Rechazar la evaluación con un motivo",
)
async def reject_evaluation(
    actor: CurrentActor,
    evaluation_id: UUID,
    body: RejectRequest,
    reject: Annotated[RejectEvaluation, Depends(use_case(RejectEvaluation))],
) -> DecisionResponse:
    return DecisionResponse.of(await reject.execute(actor, evaluation_id, body.reason))
