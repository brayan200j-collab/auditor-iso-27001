from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from auditor.evaluations.public import EvaluationAccess
from auditor.identity.public import Permission
from auditor.reports.application.ports import ReportRepository
from auditor.reports.domain.report import DOWNLOAD_NAME
from auditor.shared.application.ports import AuditLogger, ObjectStorage, UnitOfWork
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.audit import AuditAction, AuditEntry
from auditor.shared.domain.errors import ResourceNotFoundError


@dataclass(frozen=True, slots=True)
class SignedDownload:
    url: str
    expires_in: int


class DownloadReport:
    """Authorizes, audits and returns a short-lived signed URL; the storage path stays internal."""

    def __init__(
        self,
        access: EvaluationAccess,
        reports: ReportRepository,
        storage: ObjectStorage,
        audit: AuditLogger,
        uow: UnitOfWork,
        bucket: str,
        ttl_seconds: int,
    ) -> None:
        self._access = access
        self._reports = reports
        self._storage = storage
        self._audit = audit
        self._uow = uow
        self._bucket = bucket
        self._ttl = ttl_seconds

    async def execute(self, actor: Actor, report_id: UUID) -> SignedDownload:
        report = await self._reports.get(report_id)
        if report is None:
            raise ResourceNotFoundError()
        await self._access.require(actor, report.evaluation_id, Permission.DOWNLOAD_REPORT)
        url = await self._storage.create_signed_url(
            self._bucket, report.storage_path, self._ttl, DOWNLOAD_NAME
        )
        await self._audit.record(
            AuditEntry(
                action=AuditAction.REPORT_DOWNLOADED,
                actor_id=actor.user_id,
                actor_role=actor.role.value,
                company_id=report.company_id,
                resource_type="report",
                resource_id=report.id,
                details={"version": report.version},
            )
        )
        await self._uow.commit()
        return SignedDownload(url=url, expires_in=self._ttl)
