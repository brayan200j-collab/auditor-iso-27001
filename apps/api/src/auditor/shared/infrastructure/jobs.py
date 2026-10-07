"""`processing_jobs` persistence and the in-process asyncio job runner."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from auditor.shared.application.jobs import JobRecord, PermanentJobError
from auditor.shared.application.ports import Clock
from auditor.shared.domain.vocabulary import JobKind, JobStatus
from auditor.shared.infrastructure.jobs_model import ProcessingJobModel

logger = structlog.get_logger(__name__)

INTERRUPTED = "INTERRUPTED"
_ERROR_LIMIT = 300


def _to_record(model: ProcessingJobModel) -> JobRecord:
    return JobRecord(
        id=model.id,
        evaluation_id=model.evaluation_id,
        analysis_run_id=model.analysis_run_id,
        kind=JobKind(model.kind),
        status=JobStatus(model.status),
        attempts=model.attempts,
        max_attempts=model.max_attempts,
        last_error=model.last_error,
        queued_at=model.queued_at,
        started_at=model.started_at,
        heartbeat_at=model.heartbeat_at,
        finished_at=model.finished_at,
    )


class SqlJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def enqueue(
        self,
        evaluation_id: UUID,
        analysis_run_id: UUID,
        kind: JobKind,
        max_attempts: int,
        requested_by: UUID | None,
    ) -> JobRecord:
        active = await self._session.scalar(
            select(ProcessingJobModel).where(
                ProcessingJobModel.evaluation_id == evaluation_id,
                ProcessingJobModel.analysis_run_id == analysis_run_id,
                ProcessingJobModel.kind == kind,
                ProcessingJobModel.status.in_([JobStatus.QUEUED, JobStatus.RUNNING]),
            )
        )
        if active is not None:
            return _to_record(active)
        model = ProcessingJobModel(
            evaluation_id=evaluation_id,
            analysis_run_id=analysis_run_id,
            kind=kind,
            status=JobStatus.QUEUED,
            max_attempts=max_attempts,
            requested_by=requested_by,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_record(model)

    async def claim(self, job_id: UUID, now: datetime) -> JobRecord | None:
        result = await self._session.execute(
            update(ProcessingJobModel)
            .where(ProcessingJobModel.id == job_id, ProcessingJobModel.status == JobStatus.QUEUED)
            .values(
                status=JobStatus.RUNNING,
                attempts=ProcessingJobModel.attempts + 1,
                started_at=now,
                heartbeat_at=now,
            )
            .returning(ProcessingJobModel)
        )
        model = result.scalar_one_or_none()
        return _to_record(model) if model else None

    async def heartbeat(self, job_id: UUID, now: datetime) -> None:
        await self._session.execute(
            update(ProcessingJobModel)
            .where(ProcessingJobModel.id == job_id, ProcessingJobModel.status == JobStatus.RUNNING)
            .values(heartbeat_at=now)
        )

    async def succeed(self, job_id: UUID, now: datetime) -> None:
        await self._session.execute(
            update(ProcessingJobModel)
            .where(ProcessingJobModel.id == job_id)
            .values(status=JobStatus.SUCCEEDED, finished_at=now, last_error=None)
        )

    async def requeue(self, job_id: UUID, error: str) -> None:
        await self._session.execute(
            update(ProcessingJobModel)
            .where(ProcessingJobModel.id == job_id)
            .values(status=JobStatus.QUEUED, last_error=error[:_ERROR_LIMIT], heartbeat_at=None)
        )

    async def fail(self, job_id: UUID, error: str, now: datetime) -> None:
        await self._session.execute(
            update(ProcessingJobModel)
            .where(ProcessingJobModel.id == job_id)
            .values(status=JobStatus.FAILED, last_error=error[:_ERROR_LIMIT], finished_at=now)
        )

    async def get(self, job_id: UUID) -> JobRecord | None:
        model = await self._session.get(ProcessingJobModel, job_id, populate_existing=True)
        return _to_record(model) if model else None

    async def recoverable(self, stale_before: datetime) -> list[JobRecord]:
        models = await self._session.scalars(
            select(ProcessingJobModel)
            .where(
                or_(
                    ProcessingJobModel.status == JobStatus.QUEUED,
                    (ProcessingJobModel.status == JobStatus.RUNNING)
                    & (ProcessingJobModel.heartbeat_at < stale_before),
                )
            )
            .order_by(ProcessingJobModel.queued_at)
        )
        return [_to_record(model) for model in models]


JobHandler = Callable[[JobRecord], Awaitable[None]]
FailureHandler = Callable[[JobRecord, str], Awaitable[None]]


class AsyncioJobRunner:
    """Runs jobs as asyncio tasks inside the API process (no broker; see docs/DECISIONS.md).

    Durability comes from `processing_jobs` plus `recover()`, called at startup and periodically.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        clock: Clock,
        *,
        stale_after_seconds: int,
        heartbeat_seconds: float = 10.0,
        retry_delay_seconds: float = 2.0,
    ) -> None:
        self._sessions = session_factory
        self._clock = clock
        self._stale_after = timedelta(seconds=stale_after_seconds)
        self._heartbeat_seconds = heartbeat_seconds
        self._retry_delay = retry_delay_seconds
        self._handlers: dict[JobKind, JobHandler] = {}
        self._on_failed: FailureHandler | None = None
        self._tasks: set[asyncio.Task[None]] = set()
        self._sweeper: asyncio.Task[None] | None = None

    def register(self, kind: JobKind, handler: JobHandler) -> None:
        self._handlers[kind] = handler

    def on_failed(self, handler: FailureHandler) -> None:
        self._on_failed = handler

    def submit(self, job_id: UUID) -> None:
        task = asyncio.get_running_loop().create_task(self._execute(job_id), name=str(job_id))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def drain(self) -> None:
        """Waits until no job task is pending (used by tests and graceful shutdown)."""
        while self._tasks:
            await asyncio.gather(*list(self._tasks), return_exceptions=True)

    async def _execute(self, job_id: UUID) -> None:
        async with self._sessions() as session:
            job = await SqlJobRepository(session).claim(job_id, self._clock.now())
            await session.commit()
        if job is None:
            return
        handler = self._handlers.get(job.kind)
        if handler is None:
            logger.warning("job_without_handler", job_id=str(job.id), kind=job.kind)
            await self._update(lambda repo: repo.requeue(job.id, "no handler registered"))
            return
        log = logger.bind(job_id=str(job.id), kind=job.kind, attempt=job.attempts)
        heartbeat = asyncio.get_running_loop().create_task(self._beat(job.id))
        try:
            await handler(job)
        except PermanentJobError as error:
            log.warning("job_failed_permanently", reason=error.reason)
            await self._finalize_failure(job, error.reason)
        except Exception as error:
            log.exception("job_failed")
            await self._retry_or_fail(job, f"{type(error).__name__}")
        else:
            await self._update(lambda repo: repo.succeed(job.id, self._clock.now()))
            log.info("job_succeeded")
        finally:
            heartbeat.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await heartbeat

    async def _beat(self, job_id: UUID) -> None:
        while True:
            await asyncio.sleep(self._heartbeat_seconds)
            await self._update(lambda repo: repo.heartbeat(job_id, self._clock.now()))

    async def _retry_or_fail(self, job: JobRecord, error: str) -> None:
        if job.attempts < job.max_attempts:
            await self._update(lambda repo: repo.requeue(job.id, error))
            await asyncio.sleep(self._retry_delay * job.attempts)
            self.submit(job.id)
            return
        await self._finalize_failure(job, error)

    async def _finalize_failure(self, job: JobRecord, reason: str) -> None:
        await self._update(lambda repo: repo.fail(job.id, reason, self._clock.now()))
        if self._on_failed is not None:
            await self._on_failed(job, reason)

    async def _requeue(self, job_id: UUID, error: str) -> None:
        await self._update(lambda repo: repo.requeue(job_id, error))

    async def _update(self, operation: Callable[[SqlJobRepository], Awaitable[None]]) -> None:
        async with self._sessions() as session:
            await operation(SqlJobRepository(session))
            await session.commit()

    async def recover(self) -> int:
        """Resubmits orphaned QUEUED jobs and stale RUNNING jobs; fails exhausted ones."""
        stale_before = self._clock.now() - self._stale_after
        async with self._sessions() as session:
            candidates = await SqlJobRepository(session).recoverable(stale_before)
        resubmitted = 0
        for job in candidates:
            if job.status is JobStatus.RUNNING:
                if job.attempts >= job.max_attempts:
                    await self._finalize_failure(job, INTERRUPTED)
                    continue
                await self._requeue(job.id, INTERRUPTED)
            if not any(not task.done() for task in self._tasks if task.get_name() == str(job.id)):
                self.submit(job.id)
                resubmitted += 1
        if candidates:
            logger.info("jobs_recovered", candidates=len(candidates), resubmitted=resubmitted)
        return resubmitted

    def start_sweeper(self, interval_seconds: float) -> None:
        async def sweep() -> None:
            while True:
                await asyncio.sleep(interval_seconds)
                try:
                    await self.recover()
                except Exception:
                    logger.exception("job_sweep_failed")

        self._sweeper = asyncio.get_running_loop().create_task(sweep())

    async def stop(self) -> None:
        if self._sweeper is not None:
            self._sweeper.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._sweeper
        for task in list(self._tasks):
            task.cancel()
        await asyncio.gather(*list(self._tasks), return_exceptions=True)
