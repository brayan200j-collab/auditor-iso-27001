from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from auditor.config import Settings

TEST_JWT_SECRET = "test-only-jwt-secret-with-enough-length-0123456789"
TEST_ISSUER = "http://auth.test.invalid/auth/v1"
DEFAULT_TEST_DB = "postgresql+psycopg://postgres:postgres@localhost:54322/auditor_test"


def test_database_url() -> str:
    return os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DB)


def make_settings(tmp_storage: Path | None = None, **overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "app_env": "test",
        "database_url": test_database_url(),
        "supabase_url": "http://supabase.test.invalid",
        "supabase_public_url": "http://supabase.test.invalid",
        "supabase_jwt_issuer": TEST_ISSUER,
        "supabase_service_role_key": "test-service-role-key",
        "allowed_origins": ["http://localhost:3000"],
        "llm_provider": "fake",
        "auth_provider": "test",
        "storage_provider": "local",
        "test_jwt_secret": TEST_JWT_SECRET,
        "local_storage_dir": tmp_storage or Path("/tmp/auditor-test-storage"),  # noqa: S108
        # Suites such as the contract fuzzer send many requests per session; dedicated tests
        # (tests/integration/test_rate_limits.py) override these with tight limits.
        "rate_limit_default": "100000/minute",
        "rate_limit_upload": "100000/minute",
        "rate_limit_start": "100000/minute",
        "rate_limit_download": "100000/minute",
    }
    values.update(overrides)
    return Settings(**values)
