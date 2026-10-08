from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from auditor.shared.infrastructure.database import Base, utc_now_column


class ReportModel(Base):
    __tablename__ = "reports"
    __table_args__ = (UniqueConstraint("evaluation_id", "version"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    evaluation_id: Mapped[UUID] = mapped_column(
        ForeignKey("evaluations.id", ondelete="CASCADE"), index=True
    )
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), index=True
    )
    analysis_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE")
    )
    version: Mapped[int] = mapped_column(Integer)
    storage_path: Mapped[str] = mapped_column(String(300))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    generated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    generated_at: Mapped[datetime] = utc_now_column()
