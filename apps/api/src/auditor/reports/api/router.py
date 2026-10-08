from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from auditor.reports.application.download_report import DownloadReport
from auditor.reports.application.get_report_status import GetReportStatus, ReportStatus
from auditor.reports.application.request_report import RequestReport
from auditor.reports.domain.report import ReportState
from auditor.shared.api.dependencies import CurrentActor, use_case
from auditor.shared.api.rate_limit import rate_limit
from auditor.shared.api.schemas import ERROR_RESPONSES, ApiModel

router = APIRouter(prefix="/api/v1", tags=["reports"], responses=ERROR_RESPONSES)


class ReportStatusResponse(ApiModel):
    state: ReportState
    report_id: UUID | None
    version: int | None
    generated_at: datetime | None

    @classmethod
    def of(cls, report_status: ReportStatus) -> ReportStatusResponse:
        report = report_status.report
        return cls(
            state=report_status.state,
            report_id=report.id if report else None,
            version=report.version if report else None,
            generated_at=report.generated_at if report else None,
        )


class DownloadResponse(ApiModel):
    url: str
    expires_in: int


@router.get(
    "/evaluations/{evaluation_id}/report",
    response_model=ReportStatusResponse,
    summary="Estado del informe PDF",
)
async def report_status(
    actor: CurrentActor,
    evaluation_id: UUID,
    get: Annotated[GetReportStatus, Depends(use_case(GetReportStatus))],
) -> ReportStatusResponse:
    return ReportStatusResponse.of(await get.execute(actor, evaluation_id))


@router.post(
    "/evaluations/{evaluation_id}/report",
    response_model=ReportStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generar el informe PDF",
)
async def request_report(
    actor: CurrentActor,
    evaluation_id: UUID,
    request: Annotated[RequestReport, Depends(use_case(RequestReport))],
    get: Annotated[GetReportStatus, Depends(use_case(GetReportStatus))],
) -> ReportStatusResponse:
    await request.execute(actor, evaluation_id)
    return ReportStatusResponse.of(await get.execute(actor, evaluation_id))


@router.get(
    "/reports/{report_id}/download",
    response_model=DownloadResponse,
    dependencies=[Depends(rate_limit("download"))],
    summary="URL firmada de corta duración para descargar el informe",
)
async def download_report(
    actor: CurrentActor,
    report_id: UUID,
    download: Annotated[DownloadReport, Depends(use_case(DownloadReport))],
) -> DownloadResponse:
    signed = await download.execute(actor, report_id)
    return DownloadResponse(url=signed.url, expires_in=signed.expires_in)
