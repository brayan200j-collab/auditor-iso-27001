from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from auditor.retention.application.purge_expired import PurgeExpiredDocuments
from auditor.shared.api.dependencies import CurrentActor, use_case
from auditor.shared.api.schemas import ERROR_RESPONSES, ApiModel

router = APIRouter(prefix="/api/v1", tags=["retention"], responses=ERROR_RESPONSES)


class PurgeResponse(ApiModel):
    evaluations: int
    documents: int


@router.post(
    "/retention/purge",
    response_model=PurgeResponse,
    summary="Eliminar documentos cuyo plazo de retención venció",
)
async def purge_expired(
    actor: CurrentActor,
    purge: Annotated[PurgeExpiredDocuments, Depends(use_case(PurgeExpiredDocuments))],
) -> PurgeResponse:
    summary = await purge.execute(actor)
    return PurgeResponse(evaluations=summary.evaluations, documents=summary.documents)
