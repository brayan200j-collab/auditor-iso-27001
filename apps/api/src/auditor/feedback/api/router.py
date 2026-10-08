from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import Field

from auditor.feedback.application.submit_feedback import GetSurveyStatus, SubmitFeedback
from auditor.feedback.domain.feedback import PayWillingness, SurveyAnswers
from auditor.shared.api.dependencies import CurrentActor, use_case
from auditor.shared.api.schemas import ERROR_RESPONSES, ApiModel, RequestModel

router = APIRouter(prefix="/api/v1", tags=["feedback"], responses=ERROR_RESPONSES)

Scale = Annotated[int, Field(ge=1, le=5)]
Hours = Annotated[Decimal, Field(ge=0, le=1000, max_digits=6, decimal_places=1)]


class FeedbackRequest(RequestModel):
    evaluation_id: UUID
    usefulness: Scale
    ease_of_use: Scale
    trust_in_results: Scale
    actionable_recommendations: bool
    manual_time_hours: Hours = Field(description="Tiempo estimado sin el sistema, en horas")
    system_time_hours: Hours = Field(description="Tiempo usando el sistema, en horas")
    willingness_to_use: Scale
    willingness_to_pay: PayWillingness
    comments: str | None = Field(default=None, max_length=2000)


class SurveyStatusResponse(ApiModel):
    available: bool
    submitted_at: datetime | None


@router.post(
    "/feedback",
    status_code=status.HTTP_201_CREATED,
    response_model=SurveyStatusResponse,
    summary="Responder la encuesta de validación",
)
async def submit_feedback(
    actor: CurrentActor,
    body: FeedbackRequest,
    submit: Annotated[SubmitFeedback, Depends(use_case(SubmitFeedback))],
    get: Annotated[GetSurveyStatus, Depends(use_case(GetSurveyStatus))],
) -> SurveyStatusResponse:
    await submit.execute(
        actor,
        body.evaluation_id,
        SurveyAnswers(
            usefulness=body.usefulness,
            ease_of_use=body.ease_of_use,
            trust_in_results=body.trust_in_results,
            actionable_recommendations=body.actionable_recommendations,
            manual_time_hours=body.manual_time_hours,
            system_time_hours=body.system_time_hours,
            willingness_to_use=body.willingness_to_use,
            willingness_to_pay=body.willingness_to_pay,
            comments=body.comments,
        ),
    )
    result = await get.execute(actor, body.evaluation_id)
    return SurveyStatusResponse(available=result.available, submitted_at=result.submitted_at)


@router.get(
    "/evaluations/{evaluation_id}/feedback",
    response_model=SurveyStatusResponse,
    summary="Estado de la encuesta de la evaluación",
)
async def survey_status(
    actor: CurrentActor,
    evaluation_id: UUID,
    get: Annotated[GetSurveyStatus, Depends(use_case(GetSurveyStatus))],
) -> SurveyStatusResponse:
    result = await get.execute(actor, evaluation_id)
    return SurveyStatusResponse(available=result.available, submitted_at=result.submitted_at)
