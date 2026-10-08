"""GroqCloud chat completions with strict structured outputs (JSON Schema).

Verified against the official documentation on 2026-10-07: `openai/gpt-oss-120b` supports
`response_format={"type": "json_schema", "json_schema": {..., "strict": true}}`; HTTP 429 carries
`retry-after`. The model has no tools and no internet access in these calls.
"""

from __future__ import annotations

from typing import Any

import httpx

from auditor.analysis.application.ports import (
    LlmRequest,
    LlmResponse,
    ProviderRejectedOutputError,
    ProviderUnavailableError,
    RateLimitedError,
)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_SERVER_ERROR = 500


def _retry_after(response: httpx.Response) -> float | None:
    value = response.headers.get("retry-after")
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


class GroqProvider:
    name = "groq"

    def __init__(
        self,
        api_key: str,
        model: str,
        http: httpx.AsyncClient,
        *,
        timeout_seconds: float = 60.0,
        reasoning_effort: str | None = "low",
        url: str = GROQ_URL,
    ) -> None:
        self.model = model
        self._key = api_key
        self._http = http
        self._timeout = timeout_seconds
        self._reasoning_effort = reasoning_effort
        self._url = url

    def _payload(self, request: LlmRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.user},
            ],
            "temperature": 0.2,
            "max_completion_tokens": request.max_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": request.schema_name,
                    "strict": True,
                    "schema": request.json_schema,
                },
            },
        }
        if self._reasoning_effort:
            payload["reasoning_effort"] = self._reasoning_effort
        return payload

    async def complete(self, request: LlmRequest) -> LlmResponse:
        try:
            response = await self._http.post(
                self._url,
                json=self._payload(request),
                headers={"authorization": f"Bearer {self._key}"},
                timeout=self._timeout,
            )
        except httpx.HTTPError as error:
            raise ProviderUnavailableError(type(error).__name__) from error
        if response.status_code == httpx.codes.TOO_MANY_REQUESTS:
            raise RateLimitedError(_retry_after(response))
        if response.status_code >= _SERVER_ERROR:
            raise ProviderUnavailableError(f"HTTP {response.status_code}")
        if not response.is_success:
            raise ProviderRejectedOutputError(f"HTTP {response.status_code}")
        body = response.json()
        try:
            content = body["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as error:
            raise ProviderRejectedOutputError("unexpected response shape") from error
        usage = body.get("usage") or {}
        return LlmResponse(
            content=content,
            provider=self.name,
            model=str(body.get("model", self.model)),
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
        )
