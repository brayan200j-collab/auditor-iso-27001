"""Public interface of the identity module (permission matrix and user DTOs)."""

from auditor.identity.domain.permissions import (
    PERMISSION_MATRIX,
    Permission,
    ResourceOwnership,
    Scope,
    authorize,
    can_access,
    scope_for,
)

__all__ = [
    "PERMISSION_MATRIX",
    "Permission",
    "ResourceOwnership",
    "Scope",
    "authorize",
    "can_access",
    "scope_for",
]
