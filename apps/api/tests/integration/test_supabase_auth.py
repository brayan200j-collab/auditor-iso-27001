"""Exercises the production token path against Supabase local (ES256 tokens verified via JWKS)."""

from __future__ import annotations

import os
import secrets

import httpx
import pytest

from auditor.identity.infrastructure.supabase_admin import SupabaseAuthAdmin
from auditor.identity.infrastructure.token_verifiers import SupabaseJwtVerifier
from auditor.shared.domain.errors import UnauthorizedError


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        pytest.fail(f"{name} must be set (run `make env` with Supabase local running)")
    return value


async def test_real_supabase_access_token_is_verified_with_jwks() -> None:
    base_url = _env("SUPABASE_URL").rstrip("/")
    service_key = _env("SUPABASE_SERVICE_ROLE_KEY")
    issuer = _env("SUPABASE_JWT_ISSUER")
    email = f"jwks-{secrets.token_hex(4)}@example.test"
    password = "Aa1" + secrets.token_urlsafe(16)

    async with httpx.AsyncClient() as http:
        admin = SupabaseAuthAdmin(base_url, service_key, http)
        user_id = await admin.create_user(email, password)
        try:
            login = await http.post(
                f"{base_url}/auth/v1/token",
                params={"grant_type": "password"},
                headers={"apikey": service_key},
                json={"email": email, "password": password},
            )
            assert login.status_code == 200
            token = login.json()["access_token"]

            verifier = SupabaseJwtVerifier(
                f"{base_url}/auth/v1/.well-known/jwks.json", issuer, "authenticated"
            )
            verified = await verifier.verify(token)
            assert verified.subject == user_id

            tampered = token[:-4] + ("AAAA" if not token.endswith("AAAA") else "BBBB")
            with pytest.raises(UnauthorizedError):
                await verifier.verify(tampered)
            wrong_issuer = SupabaseJwtVerifier(
                f"{base_url}/auth/v1/.well-known/jwks.json", "https://evil.example", "authenticated"
            )
            with pytest.raises(UnauthorizedError):
                await wrong_issuer.verify(token)
        finally:
            await http.delete(
                f"{base_url}/auth/v1/admin/users/{user_id}",
                headers={"apikey": service_key, "authorization": f"Bearer {service_key}"},
            )
