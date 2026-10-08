"""Short-lived upload tickets.

Hosting platforms limit request bodies of web functions (4.5 MB on Vercel), so the browser sends
PDFs (up to 20 MB) straight to the API. The session token stays in its HttpOnly cookie: instead,
the web server asks the API for a ticket bound to one user and one evaluation, valid for a few
minutes and signed with HMAC-SHA256. The upload endpoint accepts it in place of the bearer token.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from auditor.shared.domain.errors import UnauthorizedError

TICKET_TTL_SECONDS = 300


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(secret: bytes, payload: str) -> str:
    return _b64(hmac.new(secret, payload.encode(), hashlib.sha256).digest())


@dataclass(frozen=True, slots=True)
class UploadTicket:
    value: str
    expires_in: int


def issue_ticket(
    secret: bytes,
    user_id: UUID,
    evaluation_id: UUID,
    now: datetime,
    ttl_seconds: int = TICKET_TTL_SECONDS,
) -> UploadTicket:
    expires = int(now.timestamp()) + ttl_seconds
    payload = _b64(
        json.dumps({"sub": str(user_id), "evl": str(evaluation_id), "exp": expires}).encode()
    )
    return UploadTicket(value=f"{payload}.{_sign(secret, payload)}", expires_in=ttl_seconds)


def _checked_user(secret: bytes, ticket: str, evaluation_id: UUID, now: datetime) -> UUID:
    payload, signature = ticket.split(".", 1)
    if not hmac.compare_digest(signature, _sign(secret, payload)):
        raise ValueError("bad signature")
    claims = json.loads(_unb64(payload))
    if UUID(claims["evl"]) != evaluation_id:
        raise ValueError("other evaluation")
    if int(claims["exp"]) < int(now.timestamp()):
        raise ValueError("expired")
    return UUID(claims["sub"])


def verify_ticket(secret: bytes, ticket: str, evaluation_id: UUID, now: datetime) -> UUID:
    """Returns the user id, or raises UnauthorizedError (tampered, expired or other evaluation)."""
    try:
        return _checked_user(secret, ticket, evaluation_id, now)
    except (ValueError, KeyError, TypeError) as exc:
        raise UnauthorizedError(detail=f"invalid upload ticket: {exc}") from exc
