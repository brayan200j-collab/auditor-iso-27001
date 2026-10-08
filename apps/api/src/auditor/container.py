"""Composition root: builds adapters and wires use cases. The only place that knows them all."""

from __future__ import annotations

import asyncio
import contextlib
import secrets
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, cast

import httpx
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

import auditor.persistence  # noqa: F401 - registers every ORM model (foreign keys across modules)
from auditor.analysis.application.evaluate_criterion import (
    CriterionEvaluator,
    CriterionTask,
    EngineLimits,
)
from auditor.analysis.application.mark_processing_failed import MarkProcessingFailed
from auditor.analysis.application.ports import LLMProvider
from auditor.analysis.application.retry_processing import RetryProcessing
from auditor.analysis.application.retrying_provider import RetryingProvider
from auditor.analysis.application.run_analysis import (
    AnalysisOrchestrator,
    CompleteAnalysis,
    EvaluateAndStore,
    PlanAnalysis,
)
from auditor.analysis.application.run_extraction_step import RunExtractionStep
from auditor.analysis.application.start_analysis import StartAnalysis
from auditor.analysis.infrastructure.evidence_search import DocumentEvidenceSearch
from auditor.analysis.infrastructure.fake_provider import FakeLLMProvider
from auditor.analysis.infrastructure.gemini_provider import GeminiProvider
from auditor.analysis.infrastructure.groq_provider import GroqProvider
from auditor.analysis.infrastructure.progress import FindingProgressReader
from auditor.analysis.infrastructure.prompt_templates import FilePromptTemplates
from auditor.analysis.infrastructure.repositories import SqlFindingRepository, SqlLlmCallRecorder
from auditor.audit.application.list_audit_logs import ListAuditLogs
from auditor.audit.infrastructure.audit_log_reader import SqlAuditLogReader
from auditor.audit.infrastructure.sql_audit_logger import SqlAuditLogger
from auditor.checklist.application.create_draft import CreateChecklistDraft
from auditor.checklist.application.get_version import GetChecklistVersion
from auditor.checklist.application.list_versions import ListChecklistVersions
from auditor.checklist.application.publish_version import PublishChecklistVersion
from auditor.checklist.application.update_item import UpdateChecklistItem
from auditor.checklist.infrastructure.repository import SqlChecklistRepository
from auditor.companies.application.create_company import CreateCompany
from auditor.companies.application.get_company import GetCompany
from auditor.companies.application.list_companies import ListCompanies
from auditor.companies.application.update_company import UpdateCompany
from auditor.companies.infrastructure.repository import SqlCompanyRepository
from auditor.config import Settings
from auditor.documents.application.delete_document import DeleteDocument
from auditor.documents.application.extract_documents import ExtractRunDocuments
from auditor.documents.application.issue_upload_ticket import IssueUploadTicket
from auditor.documents.application.list_documents import ListDocuments
from auditor.documents.application.ports import FileScanner, NoopFileScanner
from auditor.documents.application.upload_document import UploadDocument, UploadLimits
from auditor.documents.infrastructure.chunk_search import FtsChunkSearch
from auditor.documents.infrastructure.pdf_extractor import PyMuPdfExtractor
from auditor.documents.infrastructure.pdf_inspector import PyMuPdfInspector
from auditor.documents.infrastructure.repository import SqlChunkRepository, SqlDocumentRepository
from auditor.evaluations.application.access import EvaluationAccess
from auditor.evaluations.application.assign_reviewer import AssignReviewer
from auditor.evaluations.application.create_evaluation import CreateEvaluation
from auditor.evaluations.application.get_evaluation import GetEvaluation
from auditor.evaluations.application.get_status import GetEvaluationStatus
from auditor.evaluations.application.give_consent import GiveConsent
from auditor.evaluations.application.lifecycle import EvaluationLifecycle
from auditor.evaluations.application.list_evaluations import ListEvaluations
from auditor.evaluations.domain.evaluation import Evaluation
from auditor.evaluations.infrastructure.repositories import (
    SqlAnalysisRunRepository,
    SqlConsentRepository,
    SqlEvaluationRepository,
)
from auditor.feedback.application.submit_feedback import GetSurveyStatus, SubmitFeedback
from auditor.feedback.infrastructure.repositories import SqlFeedbackRepository
from auditor.identity.application.create_user import CreateUser
from auditor.identity.application.get_profile import GetProfile
from auditor.identity.application.get_user import GetUser
from auditor.identity.application.list_users import ListUsers
from auditor.identity.application.ports import AuthAdmin, TokenVerifier
from auditor.identity.application.record_session_event import RecordSessionEvent
from auditor.identity.application.resolve_actor import ResolveActor
from auditor.identity.application.resolve_ticket_actor import ResolveTicketActor
from auditor.identity.application.update_user import UpdateUser
from auditor.identity.infrastructure.supabase_admin import SupabaseAuthAdmin
from auditor.identity.infrastructure.token_verifiers import SupabaseJwtVerifier, TestJwtVerifier
from auditor.identity.infrastructure.user_repository import SqlUserRepository
from auditor.metrics.application.get_dashboard import GetDashboard
from auditor.metrics.application.get_pilot_metrics import GetPilotMetrics
from auditor.metrics.infrastructure.sql_metrics_reader import SqlMetricsReader
from auditor.reports.application.download_report import DownloadReport
from auditor.reports.application.generate_report import GenerateReport
from auditor.reports.application.get_report_status import GetReportStatus
from auditor.reports.application.request_report import RequestReport
from auditor.reports.application.schedule_report import ScheduleReport
from auditor.reports.infrastructure.renderer import WeasyPrintRenderer
from auditor.reports.infrastructure.repositories import SqlReportRepository
from auditor.retention.application.purge_expired import PurgeExpiredDocuments
from auditor.retention.infrastructure.sql_retention_store import SqlRetentionStore
from auditor.review.application.approve_evaluation import ApproveEvaluation
from auditor.review.application.get_finding import GetFinding
from auditor.review.application.get_finding_history import GetFindingHistory
from auditor.review.application.get_results import GetApprovedResults
from auditor.review.application.get_review import GetReview
from auditor.review.application.list_review_queue import ListReviewQueue
from auditor.review.application.reject_evaluation import RejectEvaluation
from auditor.review.application.review_finding import ReviewFinding
from auditor.review.infrastructure.repositories import (
    SqlFinalFindingRepository,
    SqlHumanReviewRepository,
)
from auditor.shared.application.jobs import JobRecord
from auditor.shared.application.ports import ObjectStorage
from auditor.shared.domain.actor import Actor
from auditor.shared.domain.vocabulary import JobKind
from auditor.shared.infrastructure.database import (
    SessionUnitOfWork,
    SystemClock,
    create_engine,
    create_session_factory,
    ping,
)
from auditor.shared.infrastructure.jobs import AsyncioJobRunner, SqlJobRepository
from auditor.shared.infrastructure.logging import get_logger
from auditor.shared.infrastructure.storage import LocalDiskStorage, SupabaseStorage

logger = get_logger(__name__)

Factory = Callable[["RequestScope"], Any]


def build_token_verifier(settings: Settings) -> TokenVerifier:
    if settings.auth_provider == "test":
        secret = settings.test_jwt_secret
        if secret is None:
            raise RuntimeError("TEST_JWT_SECRET is required for the test token verifier.")
        return TestJwtVerifier(
            secret.get_secret_value(), settings.supabase_jwt_issuer, settings.supabase_jwt_audience
        )
    jwks_url = settings.supabase_url.rstrip("/") + "/auth/v1/.well-known/jwks.json"
    return SupabaseJwtVerifier(
        jwks_url, settings.supabase_jwt_issuer, settings.supabase_jwt_audience
    )


def build_storage(settings: Settings, http: httpx.AsyncClient) -> ObjectStorage:
    if settings.storage_provider == "local":
        return LocalDiskStorage(
            settings.local_storage_dir, secrets.token_bytes(32), "http://testserver"
        )
    return SupabaseStorage(
        settings.supabase_url,
        settings.supabase_public_url,
        settings.supabase_service_role_key.get_secret_value(),
        http,
    )


def build_llm(settings: Settings, http: httpx.AsyncClient) -> LLMProvider:
    if settings.llm_provider == "groq" and settings.llm_api_key is not None:
        return GroqProvider(
            settings.llm_api_key.get_secret_value(),
            settings.llm_model,
            http,
            timeout_seconds=settings.llm_timeout_seconds,
            reasoning_effort=settings.llm_reasoning_effort or None,
        )
    if settings.llm_provider == "gemini" and settings.llm_api_key is not None:
        # Development with synthetic documents only: config refuses it in pilot/production.
        return GeminiProvider(
            settings.llm_api_key.get_secret_value(),
            settings.llm_model,
            http,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    if settings.llm_provider == "fake":
        return FakeLLMProvider()
    raise RuntimeError(f"LLM provider '{settings.llm_provider}' is not available")


@dataclass
class AppContainer:
    settings: Settings
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    token_verifier: TokenVerifier
    http: httpx.AsyncClient
    auth_admin: AuthAdmin
    storage: ObjectStorage
    inspector: PyMuPdfInspector
    extractor: PyMuPdfExtractor
    scanner: FileScanner
    runner: AsyncioJobRunner
    llm_backend: LLMProvider
    llm: RetryingProvider
    prompts: FilePromptTemplates
    renderer: WeasyPrintRenderer = field(default_factory=WeasyPrintRenderer)
    clock: SystemClock = field(default_factory=SystemClock)
    retention_task: asyncio.Task[None] | None = None
    upload_ticket_secret: bytes = field(default_factory=lambda: secrets.token_bytes(32))
    factories: dict[type[Any], Factory] = field(default_factory=dict)

    @classmethod
    def build(cls, settings: Settings) -> AppContainer:
        engine = create_engine(
            settings.database_url,
            pool_size=settings.database_pool_size,
            use_null_pool=settings.app_env == "test",
        )
        http = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0))
        session_factory = create_session_factory(engine)
        clock = SystemClock()
        runner = AsyncioJobRunner(
            session_factory, clock, stale_after_seconds=settings.job_running_timeout_seconds
        )
        llm_backend = build_llm(settings, http)
        container = cls(
            settings=settings,
            engine=engine,
            session_factory=session_factory,
            token_verifier=build_token_verifier(settings),
            http=http,
            auth_admin=SupabaseAuthAdmin(
                settings.supabase_url, settings.supabase_service_role_key.get_secret_value(), http
            ),
            storage=build_storage(settings, http),
            inspector=PyMuPdfInspector(settings.max_pdf_pages, settings.extraction_timeout_seconds),
            extractor=PyMuPdfExtractor(settings.max_pdf_pages, settings.extraction_timeout_seconds),
            scanner=NoopFileScanner(),
            runner=runner,
            llm_backend=llm_backend,
            llm=RetryingProvider(
                llm_backend,
                max_retries=settings.llm_max_retries,
                max_backoff_seconds=settings.llm_backoff_max_seconds,
                semaphore=asyncio.Semaphore(settings.llm_max_concurrency),
            ),
            prompts=FilePromptTemplates(settings.prompts_dir),
            clock=clock,
            factories=build_factories(),
        )
        if settings.upload_ticket_secret is not None:
            container.upload_ticket_secret = (
                settings.upload_ticket_secret.get_secret_value().encode()
            )
        container.register_jobs()
        return container

    def register_jobs(self) -> None:
        async def extraction(job: JobRecord) -> None:
            async with self.scope() as scope:
                await scope.resolve(RunExtractionStep).execute(job)

        async def plan(job: JobRecord) -> list[CriterionTask] | None:
            async with self.scope() as scope:
                return await scope.resolve(PlanAnalysis).execute(job)

        async def evaluate_one(task: CriterionTask) -> None:
            async with self.scope() as scope:
                await scope.resolve(EvaluateAndStore).execute(task)

        async def complete(job: JobRecord) -> None:
            async with self.scope() as scope:
                await scope.resolve(CompleteAnalysis).execute(job)

        orchestrator = AnalysisOrchestrator(
            plan, evaluate_one, complete, concurrency=self.settings.llm_max_concurrency
        )

        async def failed(job: JobRecord, reason: str) -> None:
            async with self.scope() as scope:
                await scope.resolve(MarkProcessingFailed).execute(job, reason)

        self.runner.register(JobKind.EXTRACTION, extraction)

        async def report(job: JobRecord) -> None:
            async with self.scope() as scope:
                await scope.resolve(GenerateReport).execute(job)

        self.runner.register(JobKind.ANALYSIS, orchestrator.run)
        self.runner.register(JobKind.REPORT, report)
        self.runner.on_failed(failed)

    async def start_background(self) -> None:
        await self.runner.recover()
        self.runner.start_sweeper(self.settings.job_sweep_interval_seconds)
        self.retention_task = asyncio.get_running_loop().create_task(self._retention_loop())

    async def _retention_loop(self) -> None:
        """Purges expired documents at startup and then every retention sweep interval."""
        while True:
            try:
                async with self.scope() as scope:
                    summary = await scope.resolve(PurgeExpiredDocuments).execute()
                if summary.documents:
                    logger.info("retention_purged", documents=summary.documents)
            except Exception:
                logger.exception("retention_sweep_failed")
            await asyncio.sleep(self.settings.retention_sweep_interval_seconds)

    async def is_ready(self) -> bool:
        return await ping(self.engine)

    async def aclose(self) -> None:
        if self.retention_task is not None:
            self.retention_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.retention_task
        await self.runner.stop()
        await self.http.aclose()
        await self.engine.dispose()

    @asynccontextmanager
    async def scope(self) -> AsyncIterator[RequestScope]:
        async with self.session_factory() as session:
            yield RequestScope(container=self, session=session)

    async def request_resolver(self) -> AsyncIterator[RequestScope]:
        async with self.scope() as scope:
            yield scope


@dataclass
class RequestScope:
    """Per-request (or per-job) object graph bound to one database session."""

    container: AppContainer
    session: AsyncSession

    @property
    def settings(self) -> Settings:
        return self.container.settings

    @cached_property
    def uow(self) -> SessionUnitOfWork:
        return SessionUnitOfWork(self.session)

    @cached_property
    def audit(self) -> SqlAuditLogger:
        return SqlAuditLogger(self.session, self.container.session_factory)

    @cached_property
    def users(self) -> SqlUserRepository:
        return SqlUserRepository(self.session)

    @cached_property
    def companies(self) -> SqlCompanyRepository:
        return SqlCompanyRepository(self.session)

    @cached_property
    def evaluations(self) -> SqlEvaluationRepository:
        return SqlEvaluationRepository(self.session)

    @cached_property
    def runs(self) -> SqlAnalysisRunRepository:
        return SqlAnalysisRunRepository(self.session)

    @cached_property
    def consents(self) -> SqlConsentRepository:
        return SqlConsentRepository(self.session)

    @cached_property
    def documents(self) -> SqlDocumentRepository:
        return SqlDocumentRepository(self.session)

    @cached_property
    def chunks(self) -> SqlChunkRepository:
        return SqlChunkRepository(self.session)

    @cached_property
    def jobs(self) -> SqlJobRepository:
        return SqlJobRepository(self.session)

    @cached_property
    def findings(self) -> SqlFindingRepository:
        return SqlFindingRepository(self.session)

    @cached_property
    def feedback(self) -> SqlFeedbackRepository:
        return SqlFeedbackRepository(self.session)

    @cached_property
    def reports(self) -> SqlReportRepository:
        return SqlReportRepository(self.session)

    @cached_property
    def finals(self) -> SqlFinalFindingRepository:
        return SqlFinalFindingRepository(self.session)

    @cached_property
    def human_reviews(self) -> SqlHumanReviewRepository:
        return SqlHumanReviewRepository(self.session)

    @cached_property
    def llm_calls(self) -> SqlLlmCallRecorder:
        return SqlLlmCallRecorder(self.session, self.container.session_factory)

    @cached_property
    def checklists(self) -> SqlChecklistRepository:
        return SqlChecklistRepository(self.session)

    @cached_property
    def evaluation_access(self) -> EvaluationAccess:
        return EvaluationAccess(self.evaluations, self.audit)

    @cached_property
    def lifecycle(self) -> EvaluationLifecycle:
        return EvaluationLifecycle(self.evaluations, self.runs, self.audit, self.container.clock)

    def resolve[T](self, use_case: type[T]) -> T:
        factory = self.container.factories.get(use_case)
        if factory is None:
            raise LookupError(f"No factory registered for {use_case.__name__}")
        return cast(T, factory(self))

    async def resolve_actor(self, bearer_token: str | None) -> Actor:
        return await ResolveActor(self.container.token_verifier, self.users).execute(bearer_token)


async def _schedule(scope: RequestScope, evaluation: Evaluation, actor: Actor) -> None:
    """Approval queues the report; a failure here never undoes the approval (retry later)."""
    await scope.resolve(ScheduleReport).execute(evaluation, actor.user_id)


def build_factories() -> dict[type[Any], Factory]:
    return {
        GetProfile: lambda s: GetProfile(s.users, s.companies),
        RecordSessionEvent: lambda s: RecordSessionEvent(s.audit),
        ListAuditLogs: lambda s: ListAuditLogs(SqlAuditLogReader(s.session)),
        CreateCompany: lambda s: CreateCompany(s.companies, s.audit, s.uow),
        UpdateCompany: lambda s: UpdateCompany(s.companies, s.audit, s.uow),
        ListCompanies: lambda s: ListCompanies(s.companies),
        GetCompany: lambda s: GetCompany(s.companies),
        CreateUser: lambda s: CreateUser(
            s.users, s.container.auth_admin, s.companies, s.audit, s.uow
        ),
        UpdateUser: lambda s: UpdateUser(
            s.users, s.container.auth_admin, s.companies, s.audit, s.uow
        ),
        ListUsers: lambda s: ListUsers(s.users),
        GetUser: lambda s: GetUser(s.users),
        CreateEvaluation: lambda s: CreateEvaluation(
            s.evaluations, s.runs, s.audit, s.uow, s.settings.max_evaluations_per_company
        ),
        ListEvaluations: lambda s: ListEvaluations(s.evaluations, s.companies, s.users),
        GetEvaluation: lambda s: GetEvaluation(
            s.evaluation_access, s.runs, s.consents, s.companies, s.users
        ),
        GetEvaluationStatus: lambda s: GetEvaluationStatus(
            s.evaluation_access, s.runs, FindingProgressReader(s.session, s.checklists)
        ),
        GiveConsent: lambda s: GiveConsent(s.evaluation_access, s.consents, s.audit, s.uow),
        AssignReviewer: lambda s: AssignReviewer(
            s.evaluation_access, s.evaluations, s.users, s.audit, s.uow
        ),
        UploadDocument: lambda s: UploadDocument(
            s.evaluation_access,
            s.lifecycle,
            s.consents,
            s.documents,
            s.container.storage,
            s.container.inspector,
            s.container.scanner,
            s.audit,
            s.uow,
            UploadLimits(
                max_bytes=s.settings.max_upload_bytes,
                max_pages=s.settings.max_pdf_pages,
                max_documents=s.settings.max_documents_per_evaluation,
                bucket=s.settings.documents_bucket,
            ),
        ),
        DeleteDocument: lambda s: DeleteDocument(
            s.evaluation_access,
            s.lifecycle,
            s.documents,
            s.container.storage,
            s.audit,
            s.uow,
            s.settings.documents_bucket,
        ),
        ListDocuments: lambda s: ListDocuments(s.evaluation_access, s.lifecycle, s.documents),
        StartAnalysis: lambda s: StartAnalysis(
            s.evaluation_access,
            s.lifecycle,
            s.documents,
            s.checklists,
            s.jobs,
            s.container.runner,
            s.uow,
            s.settings.job_max_attempts,
        ),
        RetryProcessing: lambda s: RetryProcessing(
            s.evaluation_access,
            s.lifecycle,
            s.documents,
            s.jobs,
            s.container.runner,
            s.uow,
            s.settings.job_max_attempts,
        ),
        RunExtractionStep: lambda s: RunExtractionStep(
            s.lifecycle,
            ExtractRunDocuments(
                s.documents,
                s.chunks,
                s.container.storage,
                s.container.extractor,
                s.container.clock,
                s.settings.documents_bucket,
            ),
            s.jobs,
            s.container.runner,
            s.uow,
            s.settings.job_max_attempts,
        ),
        MarkProcessingFailed: lambda s: MarkProcessingFailed(s.lifecycle, s.uow),
        CriterionEvaluator: lambda s: CriterionEvaluator(
            DocumentEvidenceSearch(FtsChunkSearch(s.session)),
            s.container.llm,
            s.container.prompts,
            s.llm_calls,
            EngineLimits(
                top_k=s.settings.evidence_top_k,
                max_tokens_per_call=s.settings.max_tokens_per_call,
                max_calls_per_evaluation=s.settings.max_llm_calls_per_evaluation,
            ),
        ),
        PlanAnalysis: lambda s: PlanAnalysis(s.lifecycle, s.checklists, s.findings),
        EvaluateAndStore: lambda s: EvaluateAndStore(
            s.resolve(CriterionEvaluator), s.findings, s.uow
        ),
        CompleteAnalysis: lambda s: CompleteAnalysis(
            s.lifecycle, s.checklists, s.findings, s.audit, s.uow
        ),
        ListReviewQueue: lambda s: ListReviewQueue(
            s.resolve(ListEvaluations), s.lifecycle, s.findings, s.finals
        ),
        GetReview: lambda s: GetReview(
            s.evaluation_access, s.lifecycle, s.findings, s.finals, s.checklists, s.documents
        ),
        GetFindingHistory: lambda s: GetFindingHistory(
            s.evaluation_access, s.findings, s.human_reviews
        ),
        GetApprovedResults: lambda s: GetApprovedResults(
            s.evaluation_access,
            s.lifecycle,
            s.finals,
            s.checklists,
            s.documents,
            s.settings.retention_days,
        ),
        GetFinding: lambda s: GetFinding(
            s.findings, s.resolve(GetReview), s.resolve(GetFindingHistory)
        ),
        ReviewFinding: lambda s: ReviewFinding(
            s.evaluation_access,
            s.lifecycle,
            s.findings,
            s.finals,
            s.human_reviews,
            s.audit,
            s.uow,
            s.container.clock,
        ),
        ApproveEvaluation: lambda s: ApproveEvaluation(
            s.evaluation_access,
            s.lifecycle,
            s.findings,
            s.finals,
            s.uow,
            after_approval=lambda evaluation, actor: _schedule(s, evaluation, actor),
        ),
        IssueUploadTicket: lambda s: IssueUploadTicket(
            s.evaluation_access, s.container.upload_ticket_secret, s.container.clock
        ),
        ResolveTicketActor: lambda s: ResolveTicketActor(
            s.users, s.container.upload_ticket_secret, s.container.clock
        ),
        PurgeExpiredDocuments: lambda s: PurgeExpiredDocuments(
            SqlRetentionStore(s.session),
            s.container.storage,
            s.audit,
            s.uow,
            s.container.clock,
            s.settings.documents_bucket,
            s.settings.retention_days,
        ),
        GetDashboard: lambda s: GetDashboard(SqlMetricsReader(s.session)),
        GetPilotMetrics: lambda s: GetPilotMetrics(SqlMetricsReader(s.session)),
        SubmitFeedback: lambda s: SubmitFeedback(s.evaluation_access, s.feedback, s.audit, s.uow),
        GetSurveyStatus: lambda s: GetSurveyStatus(s.evaluation_access, s.feedback),
        ScheduleReport: lambda s: ScheduleReport(
            s.lifecycle, s.jobs, s.container.runner, s.uow, s.settings.job_max_attempts
        ),
        RequestReport: lambda s: RequestReport(s.evaluation_access, s.resolve(ScheduleReport)),
        GetReportStatus: lambda s: GetReportStatus(s.evaluation_access, s.reports, s.jobs),
        DownloadReport: lambda s: DownloadReport(
            s.evaluation_access,
            s.reports,
            s.container.storage,
            s.audit,
            s.uow,
            s.settings.reports_bucket,
            s.settings.signed_url_ttl_seconds,
        ),
        GenerateReport: lambda s: GenerateReport(
            s.lifecycle,
            s.resolve(GetApprovedResults),
            s.documents,
            s.companies,
            s.users,
            s.reports,
            s.container.renderer,
            s.container.storage,
            s.audit,
            s.uow,
            s.container.clock,
            s.settings.reports_bucket,
        ),
        RejectEvaluation: lambda s: RejectEvaluation(s.evaluation_access, s.lifecycle, s.uow),
        ListChecklistVersions: lambda s: ListChecklistVersions(s.checklists),
        GetChecklistVersion: lambda s: GetChecklistVersion(s.checklists),
        CreateChecklistDraft: lambda s: CreateChecklistDraft(s.checklists, s.audit, s.uow),
        UpdateChecklistItem: lambda s: UpdateChecklistItem(s.checklists, s.uow),
        PublishChecklistVersion: lambda s: PublishChecklistVersion(s.checklists, s.audit, s.uow),
    }
