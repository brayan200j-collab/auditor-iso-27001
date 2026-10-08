from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from auditor.shared.infrastructure.database import Base, utc_now_column


class CompanyModel(Base):
    __tablename__ = "companies"
    __table_args__ = (
        Index(
            "uq_companies_tax_id",
            "tax_id",
            unique=True,
            postgresql_where=text("tax_id IS NOT NULL"),
        ),
        Index("ix_companies_name_lower", text("lower(name)")),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(String(200))
    tax_id: Mapped[str | None] = mapped_column(String(40))
    sector: Mapped[str | None] = mapped_column(String(120))
    city: Mapped[str | None] = mapped_column(String(120))
    active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = utc_now_column()
    updated_at: Mapped[datetime] = utc_now_column()
