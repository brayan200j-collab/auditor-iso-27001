"""Gemini API adapter — development with synthetic documents only (CLAUDE.md section 4).

The free tier may use submitted content to improve Google products, so configuration refuses this
provider in `pilot` and `production` (see `config.py`). It uses `generateContent` with
`responseMimeType: application/json` and `responseJsonSchema`; Pydantic validation still runs on
every answer, with the same single corrective retry as any other provider. Not verified with a
real key in this environment (D-039).
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

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_SERVER_ERROR = 500


def _retry_after(response: httpx.Response) -> float | None:
    value = response.headers.get("retry-after")
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


class GeminiProvider:
    name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str,
        http: httpx.AsyncClient,
        *,
        timeout_seconds: float = 60.0,
        url_template: str = GEMINI_URL,
    ) -> None:
        self.model = model
        self._key = api_key
        self._http = http
        self._timeout = timeout_seconds
        self._url = url_template.format(model=model)

    def _payload(self, request: LlmRequest) -> dict[str, Any]:
        return {
            "systemInstruction": {"parts": [{"text": request.system}]},
            "contents": [{"role": "user", "parts": [{"text": request.user}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": request.max_tokens,
                "responseMimeType": "application/json",
                "responseJsonSchema": request.json_schema,
            },
        }

    async def complete(self, request: LlmRequest) -> LlmResponse:
        try:
            response = await self._http.post(
                self._url,
                json=self._payload(request),
                headers={"x-goog-api-key": self._key},
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
            parts = body["candidates"][0]["content"]["parts"]
            content = "".join(str(part.get("text", "")) for part in parts)
        except (KeyError, IndexError, TypeError) as error:
            raise ProviderRejectedOutputError("unexpected response shape") from error
        usage = body.get("usageMetadata") or {}
        return LlmResponse(
            content=content,
            provider=self.name,
            model=str(body.get("modelVersion", self.model)),
            input_tokens=usage.get("promptTokenCount"),
            output_tokens=usage.get("candidatesTokenCount"),
        )
