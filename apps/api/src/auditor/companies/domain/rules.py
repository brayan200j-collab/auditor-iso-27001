from __future__ import annotations

import re

from auditor.shared.domain.errors import ValidationFailedError

_TAX_ID = re.compile(r"^\d{5,15}(-\d)?$")
NAME_MIN_LENGTH = 2
NAME_MAX_LENGTH = 200


def normalize_tax_id(value: str | None) -> str | None:
    """Colombian NIT: digits with an optional verification digit (900123456-7)."""
    if value is None or not value.strip():
        return None
    compact = value.replace(".", "").replace(" ", "").strip()
    if not _TAX_ID.match(compact):
        raise ValidationFailedError(
            "El NIT debe tener solo números y, opcionalmente, un dígito de verificación."
        )
    return compact


def normalize_name(value: str) -> str:
    name = " ".join(value.split())
    if not NAME_MIN_LENGTH <= len(name) <= NAME_MAX_LENGTH:
        raise ValidationFailedError("El nombre debe tener entre 2 y 200 caracteres.")
    return name
