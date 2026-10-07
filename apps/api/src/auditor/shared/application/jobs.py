"""Background job port (CLAUDE.md section 10).

Every pipeline step is a row in `processing_jobs`; runners only execute jobs they manage to claim
(QUEUED → RUNNING), so a job never runs twice at the same time, and the steps themselves are
idempotent so a retry never duplicates chunks or findings.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from auditor.shared.domain.vocabulary import JobKind, JobStatus


class PermanentJobError(Exception):
    """A failure that retrying cannot fix (e.g. an unreadable document)."""

    def __init__(self, reason: str, detail: str | None = None) -> None:
        self.reason = reason
        super().__init__(detail or reason)


@dataclass(frozen=True, slots=True)
class JobRecord:
    id: UUID
    evaluation_id: UUID
    analysis_run_id: UUID
    kind: JobKind
    status: JobStatus
    attempts: int
    max_attempts: int
    last_error: str | None
    queued_at: datetime
    started_at: datetime | None
    heartbeat_at: datetime | None
    finished_at: datetime | None


class JobRepository(Protocol):
    async def enqueue(
        self,
        evaluation_id: UUID,
        analysis_run_id: UUID,
        kind: JobKind,
        max_attempts: int,
        requested_by: UUID | None,
    ) -> JobRecord:
        """Creates a QUEUED job, or returns the active one for the same step (idempotent)."""
        ...

    async def claim(self, job_id: UUID, now: datetime) -> JobRecord | None:
        """QUEUED → RUNNING (attempts + 1). None if someone else claimed it."""
        ...

    async def heartbeat(self, job_id: UUID, now: datetime) -> None: ...

    async def succeed(self, job_id: UUID, now: datetime) -> None: ...

    async def requeue(self, job_id: UUID, error: str) -> None: ...

    async def fail(self, job_id: UUID, error: str, now: datetime) -> None: ...

    async def get(self, job_id: UUID) -> JobRecord | None: ...

    async def recoverable(self, stale_before: datetime) -> list[JobRecord]:
        """QUEUED jobs and RUNNING jobs whose heartbeat is older than `stale_before`."""
        ...


class JobRunner(Protocol):
    def submit(self, job_id: UUID) -> None:
        """Schedules a claimed-on-start execution in the background (fire and forget)."""
        ...
