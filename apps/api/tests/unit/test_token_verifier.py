from __future__ import annotations

from uuid import uuid4

import jwt
import pytest

from auditor.identity.infrastructure.token_verifiers import SupabaseJwtVerifier, TestJwtVerifier
from auditor.shared.domain.errors import UnauthorizedError
from tests.support.auth import make_token
from tests.support.settings import TEST_ISSUER, TEST_JWT_SECRET

verifier = TestJwtVerifier(TEST_JWT_SECRET, TEST_ISSUER, "authenticated")


async def test_valid_token_yields_subject() -> None:
    subject = uuid4()
    verified = await verifier.verify(make_token(subject, email="a@example.test"))
    assert verified.subject == subject
    assert verified.email == "a@example.test"


@pytest.mark.parametrize(
    "token",
    [
        make_token(uuid4(), expires_in=-60),
        make_token(uuid4(), audience="anon"),
        make_token(uuid4(), issuer="https://evil.example/auth/v1"),
        make_token(uuid4(), secret="another-secret-with-enough-length-1234567890"),
        make_token("not-a-uuid"),
        make_token(uuid4(), role="service_role"),
        jwt.encode({"sub": str(uuid4())}, key="", algorithm="none"),
        "not-a-jwt",
    ],
    ids=["expired", "audience", "issuer", "signature", "subject", "role", "alg-none", "garbage"],
)
async def test_invalid_tokens_are_rejected(token: str) -> None:
    with pytest.raises(UnauthorizedError):
        await verifier.verify(token)


async def test_supabase_verifier_rejects_symmetric_tokens_without_fetching_keys() -> None:
    supabase = SupabaseJwtVerifier(
        "http://127.0.0.1:9/auth/v1/.well-known/jwks.json", TEST_ISSUER, "authenticated"
    )
    with pytest.raises(UnauthorizedError):
        await supabase.verify(make_token(uuid4()))
