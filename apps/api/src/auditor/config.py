"""Application settings. The only place that reads environment variables."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

LLMProviderName = Literal["fake", "groq", "gemini"]

_REPO_ROOT = Path(__file__).resolve().parents[4]


class AppEnv(StrEnum):
    LOCAL = "local"
    TEST = "test"
    PILOT = "pilot"
    PRODUCTION = "production"

    @property
    def handles_real_data(self) -> bool:
        return self in {AppEnv.PILOT, AppEnv.PRODUCTION}

    @property
    def allows_dev_adapters(self) -> bool:
        return self in {AppEnv.LOCAL, AppEnv.TEST}


class ConfigurationError(RuntimeError):
    """Raised at startup when the configuration is unsafe or incomplete."""


def _split_csv(value: object) -> object:
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)

    app_env: AppEnv
    database_url: str
    database_pool_size: int = Field(default=5, ge=1, le=50)

    supabase_url: str
    supabase_public_url: str
    supabase_jwt_issuer: str
    supabase_jwt_audience: str = "authenticated"
    supabase_service_role_key: SecretStr
    documents_bucket: str = "documents"
    reports_bucket: str = "reports"

    allowed_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)

    llm_provider: LLMProviderName
    llm_api_key: SecretStr | None = None
    llm_model: str = "openai/gpt-oss-120b"
    llm_providers_allowed_for_real_data: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["groq"]
    )
    llm_max_concurrency: int = Field(default=2, ge=1, le=16)
    llm_timeout_seconds: float = Field(default=60.0, gt=0)
    llm_reasoning_effort: str = "low"
    llm_max_retries: int = Field(default=4, ge=0, le=8)
    llm_backoff_max_seconds: float = Field(default=30.0, gt=0)
    max_tokens_per_call: int = Field(default=2000, ge=256, le=16000)
    max_llm_calls_per_evaluation: int = Field(default=80, ge=1)
    max_evaluations_per_company: int = Field(default=10, ge=1)
    evidence_top_k: int = Field(default=5, ge=3, le=5)

    max_upload_bytes: int = Field(default=20 * 1024 * 1024, ge=1024)
    max_pdf_pages: int = Field(default=30, ge=1)
    max_documents_per_evaluation: int = Field(default=5, ge=1)
    extraction_timeout_seconds: float = Field(default=60.0, gt=0)

    retention_days: int = Field(default=90, ge=1)
    retention_sweep_interval_seconds: int = Field(default=21600, ge=60)
    signed_url_ttl_seconds: int = Field(default=120, ge=10, le=3600)

    job_max_attempts: int = Field(default=3, ge=1)
    job_running_timeout_seconds: int = Field(default=900, ge=30)
    job_sweep_interval_seconds: int = Field(default=60, ge=5)

    rate_limit_default: str = "120/minute"
    rate_limit_auth: str = "10/minute"
    rate_limit_upload: str = "20/hour"
    rate_limit_start: str = "20/hour"
    rate_limit_download: str = "60/hour"

    prompts_dir: Path = _REPO_ROOT / "prompts"
    seeds_dir: Path = _REPO_ROOT / "seeds"

    auth_provider: Literal["supabase", "test"] = "supabase"
    storage_provider: Literal["supabase", "local"] = "supabase"
    local_storage_dir: Path = _REPO_ROOT / ".data" / "storage"
    test_jwt_secret: SecretStr | None = None

    log_level: str = "INFO"
    sentry_dsn: SecretStr | None = None

    @field_validator("allowed_origins", "llm_providers_allowed_for_real_data", mode="before")
    @classmethod
    def _parse_csv(cls, value: object) -> object:
        return _split_csv(value)

    @model_validator(mode="after")
    def _validate_safety(self) -> Self:
        if self.app_env.handles_real_data:
            if self.llm_provider not in self.llm_providers_allowed_for_real_data:
                raise ConfigurationError(
                    f"LLM provider '{self.llm_provider}' is not allowed for real data "
                    f"in '{self.app_env}'. Allowed: {self.llm_providers_allowed_for_real_data}."
                )
            if self.llm_provider in {"fake", "gemini"}:
                raise ConfigurationError(
                    f"LLM provider '{self.llm_provider}' can never be used with real data."
                )
            if not self.allowed_origins:
                raise ConfigurationError("ALLOWED_ORIGINS is required outside local/test.")
        uses_dev_adapters = self.auth_provider != "supabase" or self.storage_provider != "supabase"
        if uses_dev_adapters and not self.app_env.allows_dev_adapters:
            raise ConfigurationError(
                "Development adapters (test auth, local storage) are only allowed "
                "when APP_ENV is local or test."
            )
        if self.auth_provider == "test" and self.app_env is not AppEnv.TEST:
            raise ConfigurationError("The test token verifier is only allowed in APP_ENV=test.")
        if self.llm_provider in {"groq", "gemini"} and not self.llm_api_key:
            raise ConfigurationError(f"LLM_API_KEY is required for provider '{self.llm_provider}'.")
        return self


def load_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue] - values come from the environment


class SeedSettings(BaseSettings):
    """Development users for `python -m auditor.seed users` (local/test only)."""

    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)

    seed_admin_email: str = ""
    seed_admin_password: SecretStr = SecretStr("")
    seed_reviewer_email: str = ""
    seed_reviewer_password: SecretStr = SecretStr("")
    seed_sme_email: str = ""
    seed_sme_password: SecretStr = SecretStr("")
    seed_sme_b_email: str = ""
    seed_sme_b_password: SecretStr = SecretStr("")
    seed_mentor_email: str = ""
    seed_mentor_password: SecretStr = SecretStr("")
