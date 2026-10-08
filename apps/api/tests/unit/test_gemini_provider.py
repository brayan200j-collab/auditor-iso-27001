"""GeminiProvider: request shape, error mapping and development-only restriction (no network)."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from auditor.analysis.application.ports import (
    LlmRequest,
    ProviderRejectedOutputError,
    ProviderUnavailableError,
    RateLimitedError,
)
from auditor.analysis.application.schemas import strict_json_schema
from auditor.analysis.infrastructure.gemini_provider import GeminiProvider
from auditor.config import ConfigurationError
from auditor.container import build_llm
from tests.support.settings import make_settings

REQUEST = LlmRequest("sistema", "usuario", strict_json_schema(), "auditor_finding", 1500)


def _gemini(handler: Any) -> GeminiProvider:
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return GeminiProvider(
        "test-key",
        "gemini-2.5-flash",
        http,
        url_template="https://gemini.test/models/{model}:generateContent",
    )


async def test_request_asks_for_schema_constrained_json() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["key"] = request.headers["x-goog-api-key"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": '{"ok": '}, {"text": "true}"}]}}],
                "usageMetadata": {"promptTokenCount": 800, "candidatesTokenCount": 90},
                "modelVersion": "gemini-2.5-flash",
            },
        )

    response = await _gemini(handler).complete(REQUEST)
    body = seen["body"]
    config = body["generationConfig"]
    assert seen["url"] == "https://gemini.test/models/gemini-2.5-flash:generateContent"
    assert seen["key"] == "test-key"
    assert config["responseMimeType"] == "application/json"
    assert config["responseJsonSchema"] == strict_json_schema()
    assert config["maxOutputTokens"] == 1500
    assert body["systemInstruction"]["parts"][0]["text"] == "sistema"
    assert [c["role"] for c in body["contents"]] == ["user"]
    assert "tools" not in body
    assert response.content == '{"ok": true}'
    assert (response.provider, response.input_tokens, response.output_tokens) == (
        "gemini",
        800,
        90,
    )


@pytest.mark.parametrize(
    ("status", "headers", "error"),
    [
        (429, {"retry-after": "30"}, RateLimitedError),
        (500, {}, ProviderUnavailableError),
        (400, {}, ProviderRejectedOutputError),
    ],
)
async def test_errors_are_translated(
    status: int, headers: dict[str, str], error: type[Exception]
) -> None:
    provider = _gemini(lambda _: httpx.Response(status, headers=headers, json={"error": {}}))
    with pytest.raises(error):
        await provider.complete(REQUEST)


async def test_unexpected_shape_is_rejected() -> None:
    provider = _gemini(lambda _: httpx.Response(200, json={"candidates": []}))
    with pytest.raises(ProviderRejectedOutputError):
        await provider.complete(REQUEST)


def test_selected_for_local_development() -> None:
    settings = make_settings(llm_provider="gemini", llm_api_key="k", llm_model="gemini-2.5-flash")
    provider = build_llm(settings, httpx.AsyncClient())
    assert isinstance(provider, GeminiProvider)


@pytest.mark.parametrize("env", ["pilot", "production"])
def test_never_starts_with_real_data_even_if_allowed(env: str) -> None:
    with pytest.raises(ConfigurationError, match="never be used with real data"):
        make_settings(
            app_env=env,
            llm_provider="gemini",
            llm_api_key="k",
            llm_providers_allowed_for_real_data="groq,gemini",
            auth_provider="supabase",
            storage_provider="supabase",
        )
