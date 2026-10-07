from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Protocol
from uuid import UUID

from auditor.analysis.domain.evidence import EvidenceCandidate
from auditor.analysis.domain.finding import AIFindingRecord, FindingDraft


@dataclass(frozen=True, slots=True)
class LlmRequest:
    system: str
    user: str
    json_schema: dict[str, Any]
    schema_name: str
    max_tokens: int
    # Structured context for deterministic test doubles; real providers only send `system`/`user`.
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LlmResponse:
    content: str
    provider: str
    model: str
    input_tokens: int | None
    output_tokens: int | None


class RateLimitedError(Exception):
    """The provider asked us to slow down (HTTP 429)."""

    def __init__(self, retry_after_seconds: float | None) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"rate limited (retry after {retry_after_seconds})")


class ProviderUnavailableError(Exception):
    """Transient provider failure (timeout, 5xx, network)."""


class ProviderRejectedOutputError(Exception):
    """The provider refused or could not produce schema-conforming output (e.g. HTTP 400)."""


class LLMProvider(Protocol):
    name: str
    model: str

    async def complete(self, request: LlmRequest) -> LlmResponse: ...


@dataclass(frozen=True, slots=True)
class LlmCallRecord:
    evaluation_id: UUID
    analysis_run_id: UUID
    criterion_code: str
    provider: str
    model: str
    prompt_version: str
    attempt: int
    input_tokens: int | None
    output_tokens: int | None
    duration_ms: int
    estimated_cost_usd: Decimal | None
    outcome: str
    error_summary: str | None
    structured_result: dict[str, Any] | None


class LlmCallRecorder(Protocol):
    async def record(self, call: LlmCallRecord) -> None:
        """Persists immediately (own transaction): usage must survive a failed analysis."""
        ...

    async def count_for_evaluation(self, evaluation_id: UUID) -> int: ...


class EvidenceSearch(Protocol):
    async def search(
        self, analysis_run_id: UUID, keywords: tuple[str, ...], limit: int
    ) -> list[EvidenceCandidate]: ...


class FindingRepository(Protocol):
    async def add(self, finding: FindingDraft) -> AIFindingRecord: ...

    async def evaluated_item_ids(self, analysis_run_id: UUID) -> set[UUID]: ...

    async def list_for_run(self, analysis_run_id: UUID) -> list[AIFindingRecord]: ...


class PromptTemplates(Protocol):
    version: str

    def system(self) -> str: ...

    def evaluation(self, values: dict[str, str]) -> str: ...
