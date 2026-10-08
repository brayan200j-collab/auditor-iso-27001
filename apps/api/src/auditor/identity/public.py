"""Public interface of the identity module (permission matrix and user DTOs)."""

from auditor.identity.application.resolve_ticket_actor import ResolveTicketActor
from auditor.identity.domain.permissions import (
    PERMISSION_MATRIX,
    Permission,
    ResourceOwnership,
    Scope,
    authorize,
    can_access,
    scope_for,
)
from auditor.identity.domain.upload_ticket import UploadTicket, issue_ticket

__all__ = [
    "PERMISSION_MATRIX",
    "Permission",
    "ResolveTicketActor",
    "ResourceOwnership",
    "Scope",
    "UploadTicket",
    "authorize",
    "can_access",
    "issue_ticket",
    "scope_for",
]
