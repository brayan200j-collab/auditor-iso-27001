from __future__ import annotations

from typing import Any, cast

import pytest
from pydantic import SecretStr

from auditor.config import SeedSettings
from auditor.seed import dev_users, seed_users
from auditor.shared.domain.actor import Role
from tests.support.settings import make_settings


@pytest.mark.parametrize("env", ["pilot", "production"])
async def test_development_users_are_never_seeded_with_real_data(env: str) -> None:
    settings = make_settings(
        app_env=env,
        llm_provider="groq",
        llm_api_key="k",
        auth_provider="supabase",
        storage_provider="supabase",
    )
    with pytest.raises(SystemExit, match="Refusing"):
        await seed_users(cast(Any, None), settings)


def test_only_fully_configured_users_are_seeded(monkeypatch: pytest.MonkeyPatch) -> None:
    for role in ("ADMIN", "REVIEWER", "SME", "SME_B", "MENTOR"):
        monkeypatch.delenv(f"SEED_{role}_EMAIL", raising=False)
        monkeypatch.delenv(f"SEED_{role}_PASSWORD", raising=False)
    seed = SeedSettings(
        seed_admin_email="Admin@Example.test",
        seed_admin_password=SecretStr("x" * 16),
        seed_sme_email="pyme@example.test",
        seed_sme_password=SecretStr(""),
    )
    users = dev_users(seed)
    assert [(user.email, user.role) for user in users] == [("admin@example.test", Role.ADMIN)]
