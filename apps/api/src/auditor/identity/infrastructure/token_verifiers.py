"""Access-token verifiers.

`SupabaseJwtVerifier` validates Supabase Auth tokens with the project's JWKS (asymmetric keys only,
which rules out algorithm-confusion attacks). `TestJwtVerifier` is accepted only when APP_ENV=test
(enforced by `Settings`).
"""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

import jwt

from auditor.identity.application.ports import VerifiedToken
from auditor.shared.domain.errors import UnauthorizedError

_ASYMMETRIC_ALGORITHMS = ["ES256", "RS256", "EdDSA"]
_LEEWAY_SECONDS = 10
_REQUIRED_CLAIMS = ["exp", "iat", "sub", "aud", "iss"]


def _to_verified(claims: dict[str, Any]) -> VerifiedToken:
    try:
        subject = UUID(str(claims["sub"]))
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError(detail="invalid subject claim") from exc
    if claims.get("role") not in (None, "authenticated"):
        raise UnauthorizedError(detail="unexpected role claim")
    email = claims.get("email")
    return VerifiedToken(subject=subject, email=email if isinstance(email, str) else None)


class SupabaseJwtVerifier:
    def __init__(self, jwks_url: str, issuer: str, audience: str) -> None:
        self._jwks = jwt.PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=600, timeout=5)
        self._issuer = issuer
        self._audience = audience

    async def verify(self, token: str) -> VerifiedToken:
        try:
            signing_key = await asyncio.to_thread(self._jwks.get_signing_key_from_jwt, token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=_ASYMMETRIC_ALGORITHMS,
                audience=self._audience,
                issuer=self._issuer,
                leeway=_LEEWAY_SECONDS,
                options={"require": _REQUIRED_CLAIMS},
            )
        except jwt.PyJWTError as exc:
            raise UnauthorizedError(detail=f"token rejected: {type(exc).__name__}") from exc
        return _to_verified(claims)


class TestJwtVerifier:
    __test__ = False  # not a pytest test class

    def __init__(self, secret: str, issuer: str, audience: str) -> None:
        self._secret = secret
        self._issuer = issuer
        self._audience = audience

    async def verify(self, token: str) -> VerifiedToken:
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=["HS256"],
                audience=self._audience,
                issuer=self._issuer,
                leeway=_LEEWAY_SECONDS,
                options={"require": _REQUIRED_CLAIMS},
            )
        except jwt.PyJWTError as exc:
            raise UnauthorizedError(detail=f"token rejected: {type(exc).__name__}") from exc
        return _to_verified(claims)
