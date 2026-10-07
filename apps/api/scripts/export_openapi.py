"""Write the OpenAPI document of the API to apps/api/openapi.json (used by `make gen-api`)."""

from __future__ import annotations

import json
import secrets
import sys
from pathlib import Path

from auditor.config import Settings
from auditor.main import create_app

OUTPUT = Path(__file__).resolve().parent.parent / "openapi.json"


def main() -> None:
    settings = Settings(
        app_env="test",
        database_url="postgresql+psycopg://openapi:unused@localhost:1/unused",
        supabase_url="http://supabase.invalid",
        supabase_public_url="http://supabase.invalid",
        supabase_jwt_issuer="http://supabase.invalid/auth/v1",
        supabase_service_role_key="unused",
        llm_provider="fake",
        auth_provider="test",
        storage_provider="local",
        test_jwt_secret=secrets.token_urlsafe(32),
    )
    schema = create_app(settings).openapi()
    OUTPUT.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    sys.stdout.write(f"OpenAPI written to {OUTPUT}\n")


if __name__ == "__main__":
    main()
