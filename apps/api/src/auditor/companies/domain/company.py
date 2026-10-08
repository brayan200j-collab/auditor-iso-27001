from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Company:
    id: UUID
    name: str
    tax_id: str | None
    sector: str | None
    city: str | None
    active: bool
    created_at: datetime
