from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from auditor.evaluations.domain.status import EvaluationStatus
from auditor.shared.infrastructure.database import Base, enum_check, utc_now_column


class EvaluationModel(Base):
    __tablename__ = "evaluations"
    __table_args__ = (enum_check("status", EvaluationStatus, "status_valid"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), index=True
    )
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    reviewer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), index=True)
    current_run_number: Mapped[int] = mapped_column(Integer, server_default="1")
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    failure_reason: Mapped[str | None] = mapped_column(String(60))
    failed_stage: Mapped[str | None] = mapped_column(String(20))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = utc_now_column()
    updated_at: Mapped[datetime] = utc_now_column()


class AnalysisRunModel(Base):
    """One processing attempt of an evaluation. A rejection followed by a new PDF opens run N+1."""

    __tablename__ = "analysis_runs"
    __table_args__ = (UniqueConstraint("evaluation_id", "run_number"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    evaluation_id: Mapped[UUID] = mapped_column(
        ForeignKey("evaluations.id", ondelete="CASCADE"), index=True
    )
    run_number: Mapped[int] = mapped_column(Integer)
    checklist_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("checklist_versions.id", ondelete="RESTRICT")
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = utc_now_column()


class ConsentModel(Base):
    """Explicit, versioned consent given before uploading documents."""

    __tablename__ = "consents"
    __table_args__ = (UniqueConstraint("evaluation_id", "user_id", "text_version"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    evaluation_id: Mapped[UUID] = mapped_column(
        ForeignKey("evaluations.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    text_version: Mapped[str] = mapped_column(String(20))
    text_sha256: Mapped[str] = mapped_column(String(64))
    accepted_at: Mapped[datetime] = utc_now_column()
