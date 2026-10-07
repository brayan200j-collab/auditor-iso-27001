"""Regression: the running app must register every ORM model, not only the ones tests import."""

from __future__ import annotations

import json
import subprocess
import sys

from tests.integration.test_schema import EXPECTED_TABLES


def test_app_factory_registers_all_tables_in_a_fresh_interpreter() -> None:
    code = (
        "import json, auditor.main;"
        "from auditor.shared.infrastructure.database import Base;"
        "print(json.dumps(sorted(Base.metadata.tables)))"
    )
    output = subprocess.run(  # noqa: S603 - fixed interpreter and code
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    ).stdout
    assert set(json.loads(output)) == EXPECTED_TABLES
