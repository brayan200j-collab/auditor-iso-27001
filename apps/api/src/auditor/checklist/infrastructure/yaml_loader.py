from __future__ import annotations

from pathlib import Path

import yaml

from auditor.checklist.application.definitions import ChecklistDefinition


def load_checklist_definition(path: Path) -> ChecklistDefinition:
    """Parses and validates a checklist YAML file. Raises pydantic.ValidationError when invalid."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ChecklistDefinition.model_validate(raw)
