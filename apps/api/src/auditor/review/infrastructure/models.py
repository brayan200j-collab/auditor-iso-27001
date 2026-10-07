from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from auditor.shared.domain.vocabulary import FindingStatus, Level, Priority, ReviewStatus
from auditor.shared.infrastructure.database import Base, enum_check, utc_now_column

REVIEW_ACTIONS = ("APPROVE", "EDIT", "DISCARD")


class HumanReviewModel(Base):
    """Insert-only trail of every reviewer decision with previous and new values."""

    __tablename__ = "human_reviews"
    __table_args__ = (enum_check("action", REVIEW_ACTIONS, "action_valid"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    ai_finding_id: Mapped[UUID] = mapped_column(
        ForeignKey("ai_findings.id", ondelete="RESTRICT"), index=True
    )
    evaluation_id: Mapped[UUID] = mapped_column(
        ForeignKey("evaluations.id", ondelete="CASCADE"), index=True
    )
    reviewer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    action: Mapped[str] = mapped_column(String(10))
    comment: Mapped[str | None] = mapped_column(Text)
    previous_values: Mapped[dict[str, Any]] = mapped_column(JSONB)
    new_values: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = utc_now_column()


class FinalFindingModel(Base):
    """What the SME sees, only after the evaluation is approved."""

    __tablename__ = "final_findings"
    __table_args__ = (
        enum_check("review_status", ReviewStatus, "review_status_valid"),
        enum_check("status", FindingStatus, "status_valid"),
        enum_check("priority", Priority, "priority_valid"),
        enum_check("effort", Level, "effort_valid"),
        enum_check("risk_level", Level, "risk_level_valid"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    ai_finding_id: Mapped[UUID] = mapped_column(
        ForeignKey("ai_findings.id", ondelete="RESTRICT"), unique=True
    )
    evaluation_id: Mapped[UUID] = mapped_column(
        ForeignKey("evaluations.id", ondelete="CASCADE"), index=True
    )
    analysis_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True
    )
    checklist_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("checklist_items.id", ondelete="RESTRICT")
    )
    criterion_code: Mapped[str] = mapped_column(String(10))
    review_status: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30))
    gap: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(10))
    effort: Mapped[str] = mapped_column(String(10))
    risk_level: Mapped[str] = mapped_column(String(10))
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, server_default="[]")
    reviewer_comment: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = utc_now_column()
