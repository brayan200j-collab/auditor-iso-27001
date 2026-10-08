from __future__ import annotations

import pytest

from auditor.config import AppEnv, ConfigurationError
from tests.support.settings import make_settings


def test_test_settings_are_valid() -> None:
    settings = make_settings()
    assert settings.app_env is AppEnv.TEST
    assert settings.evidence_top_k == 5


@pytest.mark.parametrize("env", ["pilot", "production"])
@pytest.mark.parametrize("provider", ["fake", "gemini"])
def test_startup_fails_with_provider_not_allowed_for_real_data(env: str, provider: str) -> None:
    with pytest.raises(ConfigurationError):
        make_settings(
            app_env=env,
            llm_provider=provider,
            llm_api_key="k",
            auth_provider="supabase",
            storage_provider="supabase",
        )


def test_startup_fails_when_allowed_list_excludes_configured_provider() -> None:
    with pytest.raises(ConfigurationError, match="not allowed for real data"):
        make_settings(
            app_env="pilot",
            llm_provider="groq",
            llm_api_key="k",
            llm_providers_allowed_for_real_data="gemini",
            auth_provider="supabase",
            storage_provider="supabase",
        )


def test_pilot_with_groq_is_accepted() -> None:
    settings = make_settings(
        app_env="pilot",
        llm_provider="groq",
        llm_api_key="k",
        auth_provider="supabase",
        storage_provider="supabase",
    )
    assert settings.llm_providers_allowed_for_real_data == ["groq"]


@pytest.mark.parametrize(
    ("auth", "storage"), [("test", "supabase"), ("supabase", "local"), ("test", "local")]
)
def test_dev_adapters_are_rejected_outside_local_and_test(auth: str, storage: str) -> None:
    with pytest.raises(ConfigurationError):
        make_settings(
            app_env="production",
            llm_provider="groq",
            llm_api_key="k",
            auth_provider=auth,
            storage_provider=storage,
        )


def test_test_token_verifier_is_rejected_in_local() -> None:
    with pytest.raises(ConfigurationError):
        make_settings(app_env="local", auth_provider="test")


@pytest.mark.parametrize("provider", ["groq", "gemini"])
def test_real_providers_require_api_key(provider: str) -> None:
    with pytest.raises(ConfigurationError, match="LLM_API_KEY"):
        make_settings(llm_provider=provider, llm_api_key=None)


def test_csv_lists_are_parsed() -> None:
    settings = make_settings(allowed_origins="https://a.example, https://b.example")
    assert settings.allowed_origins == ["https://a.example", "https://b.example"]


def test_missing_required_variables_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    from pydantic import ValidationError

    from auditor.config import load_settings

    for name in ("APP_ENV", "DATABASE_URL", "SUPABASE_URL", "LLM_PROVIDER"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ValidationError):
        load_settings()


def test_evidence_top_k_is_bounded() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        make_settings(evidence_top_k=8)
