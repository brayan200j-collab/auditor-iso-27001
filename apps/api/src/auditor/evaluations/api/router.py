from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import Field

from auditor.evaluations.application.assign_reviewer import AssignReviewer
from auditor.evaluations.application.create_evaluation import CreateEvaluation
from auditor.evaluations.application.get_evaluation import GetEvaluation
from auditor.evaluations.application.get_status import GetEvaluationStatus
from auditor.evaluations.application.give_consent import GiveConsent
from auditor.evaluations.application.list_evaluations import ListEvaluations
from auditor.evaluations.application.ports import EvaluationFilters
from auditor.evaluations.application.views import EvaluationDetail, EvaluationSummary
from auditor.evaluations.domain.consent import CURRENT_CONSENT
from auditor.evaluations.domain.evaluation import Evaluation, FailureReason
from auditor.evaluations.domain.progress import ProgressStep, StepState
from auditor.evaluations.domain.state_machine import Trigger
from auditor.evaluations.domain.status import EvaluationStatus
from auditor.shared.api.dependencies import CurrentActor, use_case
from auditor.shared.api.pagination import PageParams
from auditor.shared.api.schemas import ERROR_RESPONSES, ApiModel, PageMeta, RequestModel

router = APIRouter(prefix="/api/v1", tags=["evaluations"], responses=ERROR_RESPONSES)


class EvaluationCreateRequest(RequestModel):
    title: str = Field(min_length=3, max_length=200)


class ConsentRequest(RequestModel):
    version: str = Field(min_length=1, max_length=20)


class ReviewerAssignmentRequest(RequestModel):
    reviewer_id: UUID


class ProgressStepResponse(ApiModel):
    step: EvaluationStatus
    state: StepState

    @classmethod
    def of(cls, step: ProgressStep) -> ProgressStepResponse:
        return cls(step=step.step, state=step.state)


class EvaluationResponse(ApiModel):
    id: UUID
    title: str
    status: EvaluationStatus
    company_id: UUID
    company_name: str | None
    reviewer_id: UUID | None
    reviewer_name: str | None
    current_run_number: int
    rejection_reason: str | None
    failure_reason: FailureReason | None
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None
    approved_at: datetime | None

    @classmethod
    def of(
        cls, evaluation: Evaluation, company_name: str | None, reviewer_name: str | None
    ) -> EvaluationResponse:
        return cls(
            id=evaluation.id,
            title=evaluation.title,
            status=evaluation.status,
            company_id=evaluation.company_id,
            company_name=company_name,
            reviewer_id=evaluation.reviewer_id,
            reviewer_name=reviewer_name,
            current_run_number=evaluation.current_run_number,
            rejection_reason=evaluation.rejection_reason,
            failure_reason=evaluation.failure_reason,
            created_at=evaluation.created_at,
            updated_at=evaluation.updated_at,
            submitted_at=evaluation.submitted_at,
            approved_at=evaluation.approved_at,
        )

    @classmethod
    def of_summary(cls, summary: EvaluationSummary) -> EvaluationResponse:
        return cls.of(summary.evaluation, summary.company_name, summary.reviewer_name)


class EvaluationPage(ApiModel):
    items: list[EvaluationResponse]
    meta: PageMeta


class EvaluationDetailResponse(ApiModel):
    evaluation: EvaluationResponse
    run_id: UUID
    consent_given: bool
    progress: list[ProgressStepResponse]
    available_actions: list[Trigger]

    @classmethod
    def of(cls, detail: EvaluationDetail) -> EvaluationDetailResponse:
        return cls(
            evaluation=EvaluationResponse.of(
                detail.evaluation, detail.company_name, detail.reviewer_name
            ),
            run_id=detail.run.id,
            consent_given=detail.consent_given,
            progress=[ProgressStepResponse.of(step) for step in detail.progress],
            available_actions=sorted(detail.available_triggers),
        )


class EvaluationStatusResponse(ApiModel):
    id: UUID
    status: EvaluationStatus
    failure_reason: FailureReason | None
    rejection_reason: str | None
    progress: list[ProgressStepResponse]
    updated_at: datetime


class ConsentTextResponse(ApiModel):
    version: str
    text: str


def evaluation_filters(
    status_filter: Annotated[
        EvaluationStatus | None, Query(alias="status", description="Filtrar por estado")
    ] = None,
    company_id: Annotated[UUID | None, Query(description="Filtrar por empresa")] = None,
) -> EvaluationFilters:
    return EvaluationFilters(status=status_filter, company_id=company_id)


@router.post(
    "/evaluations",
    response_model=EvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear evaluación",
)
async def create_evaluation(
    actor: CurrentActor,
    body: EvaluationCreateRequest,
    create: Annotated[CreateEvaluation, Depends(use_case(CreateEvaluation))],
) -> EvaluationResponse:
    evaluation = await create.execute(actor, body.title)
    return EvaluationResponse.of(evaluation, company_name=None, reviewer_name=None)


@router.get("/evaluations", response_model=EvaluationPage, summary="Listar evaluaciones")
async def list_evaluations(
    actor: CurrentActor,
    page: PageParams,
    filters: Annotated[EvaluationFilters, Depends(evaluation_filters)],
    list_use_case: Annotated[ListEvaluations, Depends(use_case(ListEvaluations))],
) -> EvaluationPage:
    result = await list_use_case.execute(actor, filters, page)
    return EvaluationPage(
        items=[EvaluationResponse.of_summary(item) for item in result.items],
        meta=PageMeta(total=result.total, page=result.page, page_size=result.page_size),
    )


@router.get(
    "/evaluations/{evaluation_id}",
    response_model=EvaluationDetailResponse,
    summary="Detalle de evaluación",
)
async def get_evaluation(
    actor: CurrentActor,
    evaluation_id: UUID,
    get: Annotated[GetEvaluation, Depends(use_case(GetEvaluation))],
) -> EvaluationDetailResponse:
    return EvaluationDetailResponse.of(await get.execute(actor, evaluation_id))


@router.get(
    "/evaluations/{evaluation_id}/status",
    response_model=EvaluationStatusResponse,
    summary="Estado de procesamiento",
)
async def get_evaluation_status(
    actor: CurrentActor,
    evaluation_id: UUID,
    get_status: Annotated[GetEvaluationStatus, Depends(use_case(GetEvaluationStatus))],
) -> EvaluationStatusResponse:
    view = await get_status.execute(actor, evaluation_id)
    evaluation = view.evaluation
    return EvaluationStatusResponse(
        id=evaluation.id,
        status=evaluation.status,
        failure_reason=evaluation.failure_reason,
        rejection_reason=evaluation.rejection_reason,
        progress=[ProgressStepResponse.of(step) for step in view.progress],
        updated_at=evaluation.updated_at,
    )


@router.get(
    "/consent", response_model=ConsentTextResponse, summary="Texto de consentimiento vigente"
)
async def consent_text(actor: CurrentActor) -> ConsentTextResponse:
    return ConsentTextResponse(version=CURRENT_CONSENT.version, text=CURRENT_CONSENT.text)


@router.post(
    "/evaluations/{evaluation_id}/consent",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Aceptar el consentimiento para cargar documentos",
)
async def give_consent(
    actor: CurrentActor,
    evaluation_id: UUID,
    body: ConsentRequest,
    consent: Annotated[GiveConsent, Depends(use_case(GiveConsent))],
) -> None:
    await consent.execute(actor, evaluation_id, body.version)


@router.put(
    "/evaluations/{evaluation_id}/reviewer",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Asignar revisor",
)
async def assign_reviewer(
    actor: CurrentActor,
    evaluation_id: UUID,
    body: ReviewerAssignmentRequest,
    assign: Annotated[AssignReviewer, Depends(use_case(AssignReviewer))],
) -> None:
    await assign.execute(actor, evaluation_id, body.reviewer_id)
