"""Public interface of the evaluations module, used by documents, analysis, review, reports and
feedback. Other modules never load evaluations directly."""

from auditor.evaluations.application.access import EvaluationAccess
from auditor.evaluations.application.lifecycle import EvaluationLifecycle
from auditor.evaluations.application.ports import (
    AnalysisProgressReader,
    AnalysisRunRepository,
    ConsentRepository,
)
from auditor.evaluations.domain.consent import CURRENT_CONSENT
from auditor.evaluations.domain.evaluation import AnalysisRun, Evaluation, FailureReason
from auditor.evaluations.domain.state_machine import Party, Trigger
from auditor.evaluations.domain.status import PROCESSING_STATUSES, EvaluationStatus

__all__ = [
    "CURRENT_CONSENT",
    "PROCESSING_STATUSES",
    "AnalysisProgressReader",
    "AnalysisRun",
    "AnalysisRunRepository",
    "ConsentRepository",
    "Evaluation",
    "EvaluationAccess",
    "EvaluationLifecycle",
    "EvaluationStatus",
    "FailureReason",
    "Party",
    "Trigger",
]
