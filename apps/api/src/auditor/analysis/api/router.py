from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from auditor.analysis.application.retry_processing import RetryProcessing
from auditor.analysis.application.start_analysis import StartAnalysis
from auditor.evaluations.public import Evaluation, EvaluationStatus
from auditor.shared.api.dependencies import CurrentActor, use_case
from auditor.shared.api.rate_limit import rate_limit
from auditor.shared.api.schemas import ERROR_RESPONSES, ApiModel

router = APIRouter(prefix="/api/v1/evaluations", tags=["analysis"], responses=ERROR_RESPONSES)


class ProcessingResponse(ApiModel):
    id: UUID
    status: EvaluationStatus

    @classmethod
    def of(cls, evaluation: Evaluation) -> ProcessingResponse:
        return cls(id=evaluation.id, status=evaluation.status)


@router.post(
    "/{evaluation_id}/start",
    response_model=ProcessingResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limit("start"))],
    summary="Iniciar el análisis de los documentos cargados",
)
async def start_analysis(
    actor: CurrentActor,
    evaluation_id: UUID,
    start: Annotated[StartAnalysis, Depends(use_case(StartAnalysis))],
) -> ProcessingResponse:
    return ProcessingResponse.of(await start.execute(actor, evaluation_id))


@router.post(
    "/{evaluation_id}/retry",
    response_model=ProcessingResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limit("start"))],
    summary="Reintentar el procesamiento desde el último paso exitoso",
)
async def retry_processing(
    actor: CurrentActor,
    evaluation_id: UUID,
    retry: Annotated[RetryProcessing, Depends(use_case(RetryProcessing))],
) -> ProcessingResponse:
    return ProcessingResponse.of(await retry.execute(actor, evaluation_id))
