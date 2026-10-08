"""Validation survey of the pilot (CLAUDE.md section 15): one answer per approved evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from auditor.shared.domain.errors import ValidationFailedError

SCALE_MIN, SCALE_MAX = 1, 5
MAX_HOURS = Decimal(1000)
COMMENTS_MAX = 2000


class PayWillingness(StrEnum):
    YES = "YES"
    MAYBE = "MAYBE"
    NO = "NO"


@dataclass(frozen=True, slots=True)
class SurveyAnswers:
    usefulness: int
    ease_of_use: int
    trust_in_results: int
    actionable_recommendations: bool
    manual_time_hours: Decimal
    system_time_hours: Decimal
    willingness_to_use: int
    willingness_to_pay: PayWillingness
    comments: str | None

    def validated(self) -> SurveyAnswers:
        for value in (
            self.usefulness,
            self.ease_of_use,
            self.trust_in_results,
            self.willingness_to_use,
        ):
            if not SCALE_MIN <= value <= SCALE_MAX:
                raise ValidationFailedError("Las valoraciones deben estar entre 1 y 5.")
        for hours in (self.manual_time_hours, self.system_time_hours):
            if not Decimal(0) <= hours <= MAX_HOURS:
                raise ValidationFailedError("El tiempo debe estar entre 0 y 1000 horas.")
        comments = (self.comments or "").strip()
        if len(comments) > COMMENTS_MAX:
            raise ValidationFailedError("Los comentarios no pueden superar 2000 caracteres.")
        return SurveyAnswers(
            usefulness=self.usefulness,
            ease_of_use=self.ease_of_use,
            trust_in_results=self.trust_in_results,
            actionable_recommendations=self.actionable_recommendations,
            manual_time_hours=self.manual_time_hours.quantize(Decimal("0.1")),
            system_time_hours=self.system_time_hours.quantize(Decimal("0.1")),
            willingness_to_use=self.willingness_to_use,
            willingness_to_pay=self.willingness_to_pay,
            comments=comments or None,
        )


@dataclass(frozen=True, slots=True)
class Feedback:
    id: UUID
    evaluation_id: UUID
    company_id: UUID
    user_id: UUID
    answers: SurveyAnswers
