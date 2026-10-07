"""Progress timeline shown on every evaluation: Recibido → Extracción → Análisis → Revisión humana
→ Aprobado. Each step is done, current, failed or pending."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from auditor.evaluations.domain.status import EvaluationStatus as S

STEPS: tuple[S, ...] = (S.RECEIVED, S.EXTRACTING, S.ANALYZING, S.PENDING_REVIEW, S.APPROVED)


class StepState(StrEnum):
    DONE = "DONE"
    CURRENT = "CURRENT"
    FAILED = "FAILED"
    PENDING = "PENDING"


@dataclass(frozen=True, slots=True)
class ProgressStep:
    step: S
    state: StepState


def _position(status: S, failed_stage: S | None) -> tuple[int, StepState]:
    if status is S.DRAFT:
        return -1, StepState.CURRENT
    if status is S.FAILED:
        return STEPS.index(failed_stage or S.EXTRACTING), StepState.FAILED
    if status is S.REJECTED:
        return STEPS.index(S.PENDING_REVIEW), StepState.FAILED
    if status is S.APPROVED:
        return len(STEPS) - 1, StepState.DONE
    return STEPS.index(status), StepState.CURRENT


def progress(status: S, failed_stage: S | None = None) -> list[ProgressStep]:
    index, state_at_index = _position(status, failed_stage)
    steps = []
    for position, step in enumerate(STEPS):
        if position < index:
            state = StepState.DONE
        elif position == index:
            state = state_at_index
        else:
            state = StepState.PENDING
        steps.append(ProgressStep(step=step, state=state))
    return steps
