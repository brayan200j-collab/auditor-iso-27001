from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from auditor.shared.domain.vocabulary import Level, Priority
from auditor.shared.infrastructure.database import Base, enum_check, utc_now_column


class ChecklistVersionModel(Base):
    __tablename__ = "checklist_versions"
    __table_args__ = (enum_check("status", ("DRAFT", "PUBLISHED"), "status_valid"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    version: Mapped[int] = mapped_column(Integer, unique=True)
    label: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = utc_now_column()


class ChecklistItemModel(Base):
    __tablename__ = "checklist_items"
    __table_args__ = (
        UniqueConstraint("version_id", "code"),
        enum_check("priority", Priority, "priority_valid"),
        enum_check("risk_level", Level, "risk_level_valid"),
        enum_check("effort", Level, "effort_valid"),
        enum_check("reference_status", ("draft", "confirmed"), "reference_status_valid"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    version_id: Mapped[UUID] = mapped_column(
        ForeignKey("checklist_versions.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(10))
    position: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    evaluation_question: Mapped[str] = mapped_column(Text)
    expected_evidence: Mapped[str] = mapped_column(Text)
    iso_reference: Mapped[str | None] = mapped_column(String(80))
    cis_reference: Mapped[str | None] = mapped_column(String(80))
    nist_reference: Mapped[str | None] = mapped_column(String(80))
    reference_status: Mapped[str] = mapped_column(String(10))
    keywords: Mapped[list[str]] = mapped_column(ARRAY(String(80)))
    priority: Mapped[str] = mapped_column(String(10))
    risk_level: Mapped[str] = mapped_column(String(10))
    effort: Mapped[str] = mapped_column(String(10))
    active: Mapped[bool] = mapped_column(Boolean, server_default="true")
