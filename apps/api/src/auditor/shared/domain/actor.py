"""Shared kernel: who is performing an operation.

Role and company always come from the database, never from client input.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class Role(StrEnum):
    ADMIN = "ADMIN"
    REVIEWER = "REVIEWER"
    SME = "SME"
    MENTOR = "MENTOR"


@dataclass(frozen=True, slots=True)
class Actor:
    user_id: UUID
    role: Role
    company_id: UUID | None = None

    @property
    def is_admin(self) -> bool:
        return self.role is Role.ADMIN

    @property
    def is_reviewer(self) -> bool:
        return self.role is Role.REVIEWER

    @property
    def is_sme(self) -> bool:
        return self.role is Role.SME


SYSTEM_ACTOR_ID = UUID(int=0)
