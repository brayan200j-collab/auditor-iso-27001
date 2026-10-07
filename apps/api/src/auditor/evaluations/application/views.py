"""Read models returned by the evaluation use cases."""

from __future__ import annotations

from dataclasses import dataclass

from auditor.evaluations.domain.evaluation import AnalysisRun, Evaluation
from auditor.evaluations.domain.progress import ProgressStep
from auditor.evaluations.domain.state_machine import Trigger


@dataclass(frozen=True, slots=True)
class EvaluationSummary:
    evaluation: Evaluation
    company_name: str | None
    reviewer_name: str | None


@dataclass(frozen=True, slots=True)
class EvaluationDetail:
    evaluation: Evaluation
    run: AnalysisRun
    company_name: str | None
    reviewer_name: str | None
    consent_given: bool
    progress: list[ProgressStep]
    available_triggers: set[Trigger]


@dataclass(frozen=True, slots=True)
class EvaluationStatusView:
    evaluation: Evaluation
    progress: list[ProgressStep]
    criteria_done: int | None = None
    criteria_total: int | None = None
