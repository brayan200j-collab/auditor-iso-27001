from __future__ import annotations

from datetime import UTC, datetime

import pytest

from auditor.evaluations.public import CURRENT_CONSENT
from auditor.retention.domain.policy import purge_cutoff, purge_date

NOW = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)


def test_cutoff_and_purge_date_are_symmetric() -> None:
    cutoff = purge_cutoff(NOW, 90)
    assert cutoff == datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
    assert purge_date(cutoff, 90) == NOW


def test_retention_must_be_positive() -> None:
    with pytest.raises(ValueError, match="retention_days"):
        purge_cutoff(NOW, 0)


def test_consent_states_the_default_retention_period() -> None:
    # Changing RETENTION_DAYS requires a new consent version (docs/PILOT.md section 2).
    assert "90 días" in CURRENT_CONSENT.text
