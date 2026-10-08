"""Hard cap on request bodies, enforced while the bytes arrive (before anything is buffered)."""

from __future__ import annotations

import json
import re

from starlette.types import ASGIApp, Message, Receive, Scope, Send

_ENVELOPE_BYTES = 64 * 1024  # multipart boundaries and headers around the file


class _BodyTooLargeError(Exception):
    pass


class BodySizeLimitMiddleware:
    def __init__(
        self, app: ASGIApp, *, default_limit: int, upload_limit: int, upload_path: str
    ) -> None:
        self.app = app
        self.default_limit = default_limit
        self.upload_limit = upload_limit + _ENVELOPE_BYTES
        self.upload_path = re.compile(upload_path)

    def _limit_for(self, path: str) -> int:
        return self.upload_limit if self.upload_path.match(path) else self.default_limit

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        limit = self._limit_for(scope.get("path", ""))
        declared = _content_length(scope)
        if declared is not None and declared > limit:
            await _reject(send)
            return

        received = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    raise _BodyTooLargeError
            return message

        async def tracking_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except _BodyTooLargeError:
            if not response_started:
                await _reject(send)


def _content_length(scope: Scope) -> int | None:
    for key, value in scope.get("headers", []):
        if key == b"content-length":
            try:
                return int(value)
            except ValueError:
                return None
    return None


async def _reject(send: Send) -> None:
    body = json.dumps(
        {
            "code": "PAYLOAD_TOO_LARGE",
            "message": "El archivo supera el tamaño máximo permitido.",
            "request_id": None,
        }
    ).encode()
    await send(
        {
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
                (b"connection", b"close"),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})
