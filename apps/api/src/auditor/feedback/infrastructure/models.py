from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from auditor.shared.infrastructure.database import Base, enum_check, utc_now_column

PAY_WILLINGNESS = ("YES", "MAYBE", "NO")


def _scale_check(column: str) -> CheckConstraint:
    return CheckConstraint(f"{column} BETWEEN 1 AND 5", name=f"{column}_scale")


class FeedbackModel(Base):
    """Validation survey: one answer per approved evaluation."""

    __tablename__ = "feedback"
    __table_args__ = (
        _scale_check("usefulness"),
        _scale_check("ease_of_use"),
        _scale_check("trust_in_results"),
        _scale_check("willingness_to_use"),
        enum_check("willingness_to_pay", PAY_WILLINGNESS, "willingness_to_pay_valid"),
        CheckConstraint("manual_time_hours >= 0", name="manual_time_non_negative"),
        CheckConstraint("system_time_hours >= 0", name="system_time_non_negative"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    evaluation_id: Mapped[UUID] = mapped_column(
        ForeignKey("evaluations.id", ondelete="CASCADE"), unique=True
    )
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), index=True
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    usefulness: Mapped[int] = mapped_column(SmallInteger)
    ease_of_use: Mapped[int] = mapped_column(SmallInteger)
    trust_in_results: Mapped[int] = mapped_column(SmallInteger)
    actionable_recommendations: Mapped[bool] = mapped_column(Boolean)
    manual_time_hours: Mapped[Decimal] = mapped_column(Numeric(6, 1))
    system_time_hours: Mapped[Decimal] = mapped_column(Numeric(6, 1))
    willingness_to_use: Mapped[int] = mapped_column(SmallInteger)
    willingness_to_pay: Mapped[str] = mapped_column(String(10))
    comments: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = utc_now_column()
