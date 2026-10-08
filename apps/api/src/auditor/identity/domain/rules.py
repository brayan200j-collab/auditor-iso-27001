"""Business rules for accounts."""

from __future__ import annotations

from uuid import UUID

from auditor.shared.domain.actor import Role
from auditor.shared.domain.errors import ValidationFailedError

FULL_NAME_MIN = 2
FULL_NAME_MAX = 200


def check_company_for_role(role: Role, company_id: UUID | None) -> None:
    """SME users belong to exactly one company; staff roles (admin, reviewer, mentor) to none."""
    if role is Role.SME and company_id is None:
        raise ValidationFailedError("Un usuario PYME debe pertenecer a una empresa.")
    if role is not Role.SME and company_id is not None:
        raise ValidationFailedError("Solo los usuarios PYME se asocian a una empresa.")


def normalize_full_name(value: str) -> str:
    name = " ".join(value.split())
    if not FULL_NAME_MIN <= len(name) <= FULL_NAME_MAX:
        raise ValidationFailedError("El nombre debe tener entre 2 y 200 caracteres.")
    return name
