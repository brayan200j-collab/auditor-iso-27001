"""Pure ASGI middlewares: request id propagation and security headers."""

from __future__ import annotations

import json
import re
import uuid
from collections.abc import MutableMapping
from typing import Any

import structlog
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = "x-request-id"
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9-]{8,64}$")

_API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
_DOCS_CSP = (
    "default-src 'none'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: "
    "https://fastapi.tiangolo.com; connect-src 'self'; frame-ancestors 'none'"
)
_DOCS_PATHS = ("/docs", "/redoc")

_logger = structlog.get_logger(__name__)


def current_request_id() -> str | None:
    value = structlog.contextvars.get_contextvars().get("request_id")
    return value if isinstance(value, str) else None


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        incoming = _header(scope, REQUEST_ID_HEADER)
        request_id = (
            incoming if incoming and _VALID_REQUEST_ID.match(incoming) else uuid.uuid4().hex
        )
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        scope.setdefault("state", {})["request_id"] = request_id

        response_started = False

        async def send_with_id(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        except Exception:
            _logger.exception("unhandled_error")
            if response_started:
                raise
            await _send_internal_error(send_with_id, request_id)
        finally:
            structlog.contextvars.clear_contextvars()


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp, *, enable_hsts: bool) -> None:
        self.app = app
        self.enable_hsts = enable_hsts

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path: str = scope.get("path", "")
        csp = _DOCS_CSP if path.startswith(_DOCS_PATHS) else _API_CSP

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["x-content-type-options"] = "nosniff"
                headers["x-frame-options"] = "DENY"
                headers["referrer-policy"] = "no-referrer"
                headers["content-security-policy"] = csp
                headers["cross-origin-opener-policy"] = "same-origin"
                headers["permissions-policy"] = "camera=(), microphone=(), geolocation=()"
                headers.setdefault("cache-control", "no-store")
                if self.enable_hsts:
                    headers["strict-transport-security"] = "max-age=63072000; includeSubDomains"
            await send(message)

        await self.app(scope, receive, send_with_headers)


async def _send_internal_error(send: Send, request_id: str) -> None:
    body = json.dumps(
        {
            "code": "INTERNAL_ERROR",
            "message": "Ocurrió un error inesperado. Intenta más tarde.",
            "request_id": request_id,
        }
    ).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": 500,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("latin-1")),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


def _header(scope: MutableMapping[str, Any], name: str) -> str | None:
    raw = name.encode("latin-1")
    for key, value in scope.get("headers", []):
        if key.lower() == raw:
            decoded: str = value.decode("latin-1")
            return decoded
    return None
