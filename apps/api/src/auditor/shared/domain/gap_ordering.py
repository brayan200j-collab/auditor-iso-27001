"""Gap ordering shared by review, results and the report (CLAUDE.md section 13): priority first
(critical first), then risk (high first), then effort (low first: quick wins come earlier)."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol

from auditor.shared.domain.vocabulary import LEVEL_RANK, PRIORITY_RANK, Level, Priority

_EFFORT_RANK = {Level.LOW: 0, Level.MEDIUM: 1, Level.HIGH: 2}
_LAST = 99


class Rankable(Protocol):
    @property
    def criterion_code(self) -> str: ...


def gap_sort_key[T: Rankable](
    priority: Callable[[T], Priority | None],
    risk: Callable[[T], Level | None],
    effort: Callable[[T], Level | None],
) -> Callable[[T], tuple[int, int, int, str]]:
    def key(item: T) -> tuple[int, int, int, str]:
        p, r, e = priority(item), risk(item), effort(item)
        return (
            PRIORITY_RANK[p] if p else _LAST,
            LEVEL_RANK[r] if r else _LAST,
            _EFFORT_RANK[e] if e else _LAST,
            item.criterion_code,
        )

    return key


def order_gaps[T: Rankable](
    items: Sequence[T],
    priority: Callable[[T], Priority | None],
    risk: Callable[[T], Level | None],
    effort: Callable[[T], Level | None],
) -> list[T]:
    return sorted(items, key=gap_sort_key(priority, risk, effort))
