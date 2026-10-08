"""Deterministic LLM test double for local development and tests (never calls the network).

It classifies a criterion with transparent keyword rules over the fragments it receives, quotes
real text from them, and — like the real model is instructed to — ignores any instruction found
inside documents. Optional scripted replies let tests simulate invalid outputs and outages.
"""

from __future__ import annotations

import json
import re
from collections import deque
from collections.abc import Iterable
from typing import Any

from auditor.analysis.application.ports import LlmRequest, LlmResponse
from auditor.analysis.domain.evidence import MAX_QUOTE_CHARS, MIN_QUOTE_CHARS, EvidenceCandidate
from auditor.checklist.public import ChecklistItem

HEDGES = (
    "en elaboración",
    "aún no",
    "no se ha definido",
    "no se ha formalizado",
    "pendiente de",
    "está en construcción",
)
_SENTENCES = re.compile(r"(?<=[.!?;])\s+")


def _matches(content: str, keywords: Iterable[str]) -> int:
    lowered = content.lower()
    return sum(1 for keyword in keywords if keyword.lower() in lowered)


def _quote(candidate: EvidenceCandidate, keywords: tuple[str, ...]) -> str | None:
    for sentence in _SENTENCES.split(candidate.content):
        if _matches(sentence, keywords) and len(sentence.strip()) >= MIN_QUOTE_CHARS:
            return sentence.strip()[:MAX_QUOTE_CHARS]
    return None


def classify(item: ChecklistItem, candidates: list[EvidenceCandidate]) -> dict[str, Any]:
    """The fragment with most keyword hits decides; hedges there ("en elaboración") mean PARTIAL."""
    matched = sorted(
        (c for c in candidates if _matches(c.content, item.keywords)),
        key=lambda c: _matches(c.content, item.keywords),
        reverse=True,
    )
    best_hits = _matches(matched[0].content, item.keywords) if matched else 0
    hedged = bool(matched) and any(hedge in matched[0].content.lower() for hedge in HEDGES)
    citations = [
        {"chunk_id": str(c.chunk_id), "quote": quote}
        for c in matched[:2]
        if (quote := _quote(c, item.keywords))
    ]
    if not matched or not citations:
        status, confidence = "NO_DOCUMENTARY_EVIDENCE", 0.55
        citations = []
    elif hedged:
        status, confidence = "PARTIAL", 0.62
    elif best_hits >= 2:  # noqa: PLR2004 - two keywords in the same fragment
        status, confidence = "FOUND", 0.86
    else:
        status, confidence = "PARTIAL", 0.58
    gaps = {
        "FOUND": (
            f"Los documentos describen «{item.name}». Conviene mantener la evidencia actualizada."
        ),
        "PARTIAL": f"La evidencia sobre «{item.name}» está incompleta o aún no está formalizada.",
        "NO_DOCUMENTARY_EVIDENCE": (
            f"No se encontró evidencia documental suficiente sobre «{item.name}» "
            "en los fragmentos analizados."
        ),
    }
    return {
        "criterion_id": item.code,
        "status": status,
        "confidence": confidence,
        "evidence": citations,
        "gap": gaps[status],
        "recommendation": f"Revisar y completar la documentación: {item.expected_evidence}",
        "preliminary_priority": "LOW" if status == "FOUND" else item.priority.value,
        "estimated_effort": item.effort.value,
        "risk_level": item.risk_level.value,
    }


class FakeLLMProvider:
    name = "fake"

    def __init__(self, model: str = "fake-deterministic-v1", script: Iterable[Any] = ()) -> None:
        self.model = model
        self._script: deque[Any] = deque(script)
        self.requests: list[LlmRequest] = []

    def queue(self, *replies: Any) -> None:
        """Next replies: a string (raw content) or an exception instance to raise."""
        self._script.extend(replies)

    async def complete(self, request: LlmRequest) -> LlmResponse:
        self.requests.append(request)
        if self._script:
            reply = self._script.popleft()
            if isinstance(reply, BaseException):
                raise reply
            content = str(reply)
        else:
            item = request.context["item"]
            candidates = request.context["candidates"]
            content = json.dumps(classify(item, candidates), ensure_ascii=False)
        return LlmResponse(
            content=content,
            provider=self.name,
            model=self.model,
            input_tokens=(len(request.system) + len(request.user)) // 4,
            output_tokens=len(content) // 4,
        )
