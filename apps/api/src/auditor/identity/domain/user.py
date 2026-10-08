from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from auditor.shared.domain.actor import Actor, Role


@dataclass(frozen=True, slots=True)
class User:
    id: UUID
    email: str
    full_name: str
    role: Role
    active: bool
    company_id: UUID | None
    created_at: datetime

    def as_actor(self) -> Actor:
        return Actor(user_id=self.id, role=self.role, company_id=self.company_id)
