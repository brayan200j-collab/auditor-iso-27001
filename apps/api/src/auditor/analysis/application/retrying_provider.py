from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

import structlog

from auditor.analysis.application.ports import (
    LLMProvider,
    LlmRequest,
    LlmResponse,
    ProviderUnavailableError,
    RateLimitedError,
)
from auditor.shared.domain.errors import AIProviderError

logger = structlog.get_logger(__name__)

Sleep = Callable[[float], Awaitable[None]]


class RetryingProvider:
    """Respects `Retry-After` on 429 and retries transient failures with bounded exponential
    backoff. Concurrency is limited by a shared semaphore (free-tier limits)."""

    def __init__(
        self,
        inner: LLMProvider,
        *,
        max_retries: int,
        max_backoff_seconds: float,
        semaphore: asyncio.Semaphore,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        self.name = inner.name
        self.model = inner.model
        self._inner = inner
        self._max_retries = max_retries
        self._max_backoff = max_backoff_seconds
        self._semaphore = semaphore
        self._sleep = sleep

    def _delay(self, attempt: int, retry_after: float | None) -> float:
        backoff = min(self._max_backoff, 2.0**attempt)
        if retry_after is not None:
            return min(self._max_backoff, max(retry_after, 0.0))
        return backoff

    async def complete(self, request: LlmRequest) -> LlmResponse:
        attempt = 0
        while True:
            try:
                async with self._semaphore:
                    return await self._inner.complete(request)
            except RateLimitedError as error:
                if attempt >= self._max_retries:
                    raise AIProviderError(detail="rate limit retries exhausted") from error
                delay = self._delay(attempt, error.retry_after_seconds)
                logger.info("llm_rate_limited", wait_seconds=delay, attempt=attempt)
            except ProviderUnavailableError as error:
                if attempt >= self._max_retries:
                    raise AIProviderError(detail="provider unavailable") from error
                delay = self._delay(attempt, None)
                logger.info("llm_unavailable_retry", wait_seconds=delay, attempt=attempt)
            await self._sleep(delay)
            attempt += 1
