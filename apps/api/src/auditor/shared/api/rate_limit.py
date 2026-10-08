"""Per-session rate limiting for sensitive and general API operations (CLAUDE.md section 9).

Requests arrive through the Next.js server, so the client IP is the same for every user: the key
is a hash of the bearer token (one bucket per session), falling back to the IP for anonymous
requests. Limits use the `limits` library (the engine behind slowapi) with in-memory storage,
which protects a single API instance; several instances need a shared store (D-040).
"""

from __future__ import annotations

import hashlib
import math
import time
from collections.abc import Awaitable, Callable
from typing import Literal

from fastapi import Request
from limits import parse
from limits.storage import MemoryStorage
from limits.strategies import FixedWindowRateLimiter
from starlette.exceptions import HTTPException

RuleName = Literal["default", "upload", "start", "download"]


class RateLimiter:
    def __init__(self, rules: dict[RuleName, str]) -> None:
        self._rules = {name: parse(rule) for name, rule in rules.items()}
        self._strategy = FixedWindowRateLimiter(MemoryStorage())

    def retry_after(self, rule: RuleName, key: str) -> int | None:
        """Consumes one hit; returns the seconds to wait when the limit is exceeded."""
        item = self._rules[rule]
        if self._strategy.hit(item, rule, key):
            return None
        reset_at = self._strategy.get_window_stats(item, rule, key).reset_time
        return max(1, math.ceil(reset_at - time.time()))


def client_key(request: Request) -> str:
    authorization = request.headers.get("authorization")
    if authorization:
        return "s:" + hashlib.sha256(authorization.encode()).hexdigest()[:32]
    return "ip:" + (request.client.host if request.client else "unknown")


def rate_limit(rule: RuleName) -> Callable[[Request], Awaitable[None]]:
    async def dependency(request: Request) -> None:
        limiter: RateLimiter = request.app.state.rate_limiter
        wait = limiter.retry_after(rule, client_key(request))
        if wait is not None:
            raise HTTPException(status_code=429, headers={"retry-after": str(wait)})

    return dependency
