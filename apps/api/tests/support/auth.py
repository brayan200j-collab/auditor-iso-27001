from __future__ import annotations

import time
from typing import Any
from uuid import UUID

import jwt

from tests.support.settings import TEST_ISSUER, TEST_JWT_SECRET


def make_token(
    subject: UUID | str,
    *,
    expires_in: int = 300,
    issuer: str = TEST_ISSUER,
    audience: str = "authenticated",
    secret: str = TEST_JWT_SECRET,
    algorithm: str = "HS256",
    **extra: Any,
) -> str:
    now = int(time.time())
    claims: dict[str, Any] = {
        "sub": str(subject),
        "aud": audience,
        "iss": issuer,
        "iat": now,
        "exp": now + expires_in,
        "role": "authenticated",
        **extra,
    }
    return jwt.encode(claims, secret, algorithm=algorithm)


def auth_headers(subject: UUID) -> dict[str, str]:
    return {"authorization": f"Bearer {make_token(subject)}"}
