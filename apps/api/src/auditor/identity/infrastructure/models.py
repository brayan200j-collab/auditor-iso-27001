from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from auditor.shared.domain.actor import Role
from auditor.shared.infrastructure.database import Base, enum_check, utc_now_column


class UserModel(Base):
    """Application profile. `id` equals the Supabase Auth user id (`sub` claim)."""

    __tablename__ = "users"
    __table_args__ = (
        enum_check("role", Role, "role_valid"),
        Index("uq_users_email_lower", text("lower(email)"), unique=True),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320))
    full_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20))
    active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = utc_now_column()
    updated_at: Mapped[datetime] = utc_now_column()


class CompanyUserModel(Base):
    """Membership of an SME user in exactly one company."""

    __tablename__ = "company_users"

    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), primary_key=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, unique=True
    )
    created_at: Mapped[datetime] = utc_now_column()
