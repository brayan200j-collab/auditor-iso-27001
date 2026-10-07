from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from auditor.shared.domain.vocabulary import FindingStatus, Level, Priority
from auditor.shared.infrastructure.database import Base, enum_check, utc_now_column

LLM_CALL_OUTCOMES = ("SUCCESS", "INVALID_OUTPUT", "RATE_LIMITED", "ERROR")


class AIFindingModel(Base):
    """Raw AI result. Immutable: a database trigger rejects UPDATE and DELETE."""

    __tablename__ = "ai_findings"
    __table_args__ = (
        UniqueConstraint("analysis_run_id", "checklist_item_id"),
        enum_check("outcome", ("OK", "ERROR"), "outcome_valid"),
        enum_check("status", FindingStatus, "status_valid"),
        enum_check("preliminary_priority", Priority, "priority_valid"),
        enum_check("estimated_effort", Level, "effort_valid"),
        enum_check("risk_level", Level, "risk_level_valid"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
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
    outcome: Mapped[str] = mapped_column(String(10))
    status: Mapped[str | None] = mapped_column(String(30))
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, server_default="[]")
    gap: Mapped[str] = mapped_column(Text, server_default="")
    recommendation: Mapped[str] = mapped_column(Text, server_default="")
    preliminary_priority: Mapped[str | None] = mapped_column(String(10))
    estimated_effort: Mapped[str | None] = mapped_column(String(10))
    risk_level: Mapped[str | None] = mapped_column(String(10))
    requires_human_review: Mapped[bool] = mapped_column(Boolean, server_default="true")
    has_unverified_citations: Mapped[bool] = mapped_column(Boolean, server_default="false")
    llm_called: Mapped[bool] = mapped_column(Boolean)
    error_summary: Mapped[str | None] = mapped_column(String(300))
    provider: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(120))
    prompt_version: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = utc_now_column()


class LlmCallModel(Base):
    """Usage and outcome of each provider call. Never stores document text or prompts."""

    __tablename__ = "llm_calls"
    __table_args__ = (enum_check("outcome", LLM_CALL_OUTCOMES, "outcome_valid"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    evaluation_id: Mapped[UUID] = mapped_column(
        ForeignKey("evaluations.id", ondelete="CASCADE"), index=True
    )
    analysis_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True
    )
    criterion_code: Mapped[str] = mapped_column(String(10))
    provider: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(120))
    prompt_version: Mapped[str] = mapped_column(String(20))
    attempt: Mapped[int] = mapped_column(Integer)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    duration_ms: Mapped[int] = mapped_column(Integer)
    estimated_cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    outcome: Mapped[str] = mapped_column(String(20))
    error_summary: Mapped[str | None] = mapped_column(String(300))
    structured_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = utc_now_column()
