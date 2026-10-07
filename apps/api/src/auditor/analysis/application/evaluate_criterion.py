from __future__ import annotations

import time
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from auditor.analysis.application.ports import (
    EvidenceSearch,
    LlmCallRecord,
    LlmCallRecorder,
    LLMProvider,
    LlmRequest,
    PromptTemplates,
    ProviderRejectedOutputError,
)
from auditor.analysis.application.prompting import correction_note, user_prompt
from auditor.analysis.application.schemas import SCHEMA_NAME, ModelFinding, strict_json_schema
from auditor.analysis.domain.evidence import EvidenceCandidate, verify_citation
from auditor.analysis.domain.finding import FindingDraft, Outcome
from auditor.checklist.public import ChecklistItem
from auditor.shared.domain.errors import AIProviderError, QuotaExceededError
from auditor.shared.domain.vocabulary import FindingStatus, Level, Priority

MAX_ATTEMPTS = 2  # one call plus one retry with the validation error (CLAUDE.md section 13)


@dataclass(frozen=True, slots=True)
class EngineLimits:
    top_k: int
    max_tokens_per_call: int
    max_calls_per_evaluation: int


@dataclass(frozen=True, slots=True)
class CriterionTask:
    evaluation_id: UUID
    analysis_run_id: UUID
    item: ChecklistItem


def _summary_for_log(finding: ModelFinding) -> dict[str, Any]:
    """Structured result without document text (quotes are excerpts and are not logged)."""
    return {
        "criterion_id": finding.criterion_id,
        "status": finding.status,
        "confidence": finding.confidence,
        "evidence_chunks": [str(citation.chunk_id) for citation in finding.evidence],
        "preliminary_priority": finding.preliminary_priority,
        "estimated_effort": finding.estimated_effort,
        "risk_level": finding.risk_level,
    }


class CriterionEvaluator:
    """Evaluates one checklist criterion against the most relevant fragments of the documents."""

    def __init__(
        self,
        search: EvidenceSearch,
        provider: LLMProvider,
        templates: PromptTemplates,
        calls: LlmCallRecorder,
        limits: EngineLimits,
    ) -> None:
        self._search = search
        self._provider = provider
        self._templates = templates
        self._calls = calls
        self._limits = limits

    async def evaluate(self, task: CriterionTask) -> FindingDraft:
        candidates = await self._search.search(
            task.analysis_run_id, task.item.keywords, self._limits.top_k
        )
        if not candidates:
            return self._without_evidence(task)
        request = LlmRequest(
            system=self._templates.system(),
            user=user_prompt(self._templates, task.item, candidates),
            json_schema=strict_json_schema(),
            schema_name=SCHEMA_NAME,
            max_tokens=self._limits.max_tokens_per_call,
            context={"item": task.item, "candidates": candidates},
        )
        last_error = "no attempt"
        for attempt in range(1, MAX_ATTEMPTS + 1):
            parsed, last_error = await self._call(task, request, attempt)
            if parsed is not None:
                return self._from_model(task, parsed, candidates)
            request = replace(request, user=request.user + correction_note(last_error))
        return self._error(task, last_error)

    async def _call(
        self, task: CriterionTask, request: LlmRequest, attempt: int
    ) -> tuple[ModelFinding | None, str]:
        await self._enforce_quota(task.evaluation_id)
        started = time.monotonic()
        usage: tuple[int | None, int | None] = (None, None)
        try:
            response = await self._provider.complete(request)
            usage = (response.input_tokens, response.output_tokens)
            parsed = _parse(response.content, task.item.code)
        except AIProviderError:
            await self._record(task, attempt, started, usage, "ERROR", "provider unavailable")
            raise
        except ProviderRejectedOutputError as error:
            await self._record(task, attempt, started, usage, "INVALID_OUTPUT", str(error))
            return None, "rejected by provider"
        except (ValidationError, ValueError) as error:
            summary = _validation_summary(error)
            await self._record(task, attempt, started, usage, "INVALID_OUTPUT", summary)
            return None, summary
        await self._record(task, attempt, started, usage, "SUCCESS", None, _summary_for_log(parsed))
        return parsed, ""

    async def _enforce_quota(self, evaluation_id: UUID) -> None:
        used = await self._calls.count_for_evaluation(evaluation_id)
        if used >= self._limits.max_calls_per_evaluation:
            raise QuotaExceededError(
                "Se alcanzó el límite de llamadas al servicio de análisis para esta evaluación."
            )

    async def _record(
        self,
        task: CriterionTask,
        attempt: int,
        started: float,
        usage: tuple[int | None, int | None],
        outcome: str,
        error: str | None,
        result: dict[str, Any] | None = None,
    ) -> None:
        await self._calls.record(
            LlmCallRecord(
                evaluation_id=task.evaluation_id,
                analysis_run_id=task.analysis_run_id,
                criterion_code=task.item.code,
                provider=self._provider.name,
                model=self._provider.model,
                prompt_version=self._templates.version,
                attempt=attempt,
                input_tokens=usage[0],
                output_tokens=usage[1],
                duration_ms=int((time.monotonic() - started) * 1000),
                estimated_cost_usd=None,
                outcome=outcome,
                error_summary=error[:300] if error else None,
                structured_result=result,
            )
        )

    def _base(self, task: CriterionTask) -> dict[str, Any]:
        return {
            "evaluation_id": task.evaluation_id,
            "analysis_run_id": task.analysis_run_id,
            "checklist_item_id": task.item.id,
            "criterion_code": task.item.code,
            "provider": self._provider.name,
            "model": self._provider.model,
            "prompt_version": self._templates.version,
        }

    def _without_evidence(self, task: CriterionTask) -> FindingDraft:
        """No relevant fragment: no call to the model (CLAUDE.md section 4)."""
        item = task.item
        return FindingDraft(
            **self._base(task),
            outcome=Outcome.OK,
            status=FindingStatus.NO_DOCUMENTARY_EVIDENCE,
            confidence=None,
            evidence=(),
            gap=(
                f"No se encontró evidencia documental suficiente sobre «{item.name}» "
                "en los documentos aportados."
            ),
            recommendation=f"Documentar y aprobar formalmente: {item.expected_evidence}",
            preliminary_priority=item.priority,
            estimated_effort=item.effort,
            risk_level=item.risk_level,
            llm_called=False,
            error_summary=None,
        )

    def _from_model(
        self, task: CriterionTask, parsed: ModelFinding, candidates: list[EvidenceCandidate]
    ) -> FindingDraft:
        by_id = {candidate.chunk_id: candidate for candidate in candidates}
        citations = tuple(
            citation
            for model_citation in parsed.evidence
            if (citation := verify_citation(model_citation.chunk_id, model_citation.quote, by_id))
        )
        unknown = len(parsed.evidence) - len(citations)
        return FindingDraft(
            **self._base(task),
            outcome=Outcome.OK,
            status=FindingStatus(parsed.status),
            confidence=Decimal(str(round(parsed.confidence, 3))),
            evidence=citations,
            gap=parsed.gap.strip(),
            recommendation=parsed.recommendation.strip(),
            preliminary_priority=Priority(parsed.preliminary_priority),
            estimated_effort=Level(parsed.estimated_effort),
            risk_level=Level(parsed.risk_level),
            llm_called=True,
            error_summary=f"{unknown} cita(s) con fragmentos inexistentes descartada(s)"
            if unknown
            else None,
        )

    def _error(self, task: CriterionTask, error: str) -> FindingDraft:
        """Invalid output twice: the criterion is left for manual review without failing the
        whole evaluation."""
        return FindingDraft(
            **self._base(task),
            outcome=Outcome.ERROR,
            status=None,
            confidence=None,
            evidence=(),
            gap="",
            recommendation="",
            preliminary_priority=task.item.priority,
            estimated_effort=task.item.effort,
            risk_level=task.item.risk_level,
            llm_called=True,
            error_summary=f"Salida no válida del modelo: {error[:200]}",
        )


def _parse(content: str, criterion_code: str) -> ModelFinding:
    parsed = ModelFinding.model_validate_json(content)
    if parsed.criterion_id != criterion_code:
        raise ValueError("criterion_id does not match the evaluated criterion")
    return parsed


def _validation_summary(error: Exception) -> str:
    if isinstance(error, ValidationError):
        fields = sorted({".".join(str(part) for part in item["loc"]) for item in error.errors()})
        return f"invalid fields: {', '.join(fields) or 'json'}"
    return str(error)
