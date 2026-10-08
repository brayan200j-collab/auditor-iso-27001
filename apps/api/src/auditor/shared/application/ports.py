"""Cross-cutting ports implemented in infrastructure and injected by the container."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from auditor.shared.domain.audit import AuditEntry


class Clock(Protocol):
    def now(self) -> datetime: ...


class UnitOfWork(Protocol):
    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


class AuditLogger(Protocol):
    async def record(self, entry: AuditEntry) -> None:
        """Adds the entry to the current transaction (persisted on commit)."""
        ...

    async def record_immediately(self, entry: AuditEntry) -> None:
        """Persists the entry in its own transaction (used for denied access and failures)."""
        ...


class ObjectStorage(Protocol):
    async def upload(self, bucket: str, path: str, data: bytes, content_type: str) -> None: ...

    async def download(self, bucket: str, path: str) -> bytes: ...

    async def delete(self, bucket: str, path: str) -> None: ...

    async def create_signed_url(
        self, bucket: str, path: str, ttl_seconds: int, download_name: str
    ) -> str: ...
