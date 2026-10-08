from __future__ import annotations

from collections.abc import Callable
from typing import cast

import pytest

from auditor.reports.infrastructure.renderer import WeasyPrintRenderer, _refuse_urls


def test_report_template_is_autoescaped() -> None:
    env = WeasyPrintRenderer()._env
    env.get_template("report.html.j2")  # the template exists under the name checked below
    decide = cast(Callable[[str | None], bool], env.autoescape)
    assert decide("report.html.j2") is True


def test_report_never_fetches_external_resources() -> None:
    with pytest.raises(ValueError, match="external resources"):
        _refuse_urls("https://attacker.example/pixel.png")
