"""Writes the synthetic PDF fixtures used by E2E tests and manual demos (`make fixtures`)."""

from __future__ import annotations

import sys
from pathlib import Path

from tests.support import pdfs

REPO = Path(__file__).resolve().parents[4]
TARGETS = (
    REPO / "apps" / "web" / "e2e" / "fixtures",
    REPO / "apps" / "api" / "tests" / "fixtures" / "generated",
)
FILES = {
    "politica_seguridad_sintetica.pdf": pdfs.policy_pdf,
    "documento_escaneado_sintetico.pdf": pdfs.scanned_pdf,
    "documento_inyeccion_sintetico.pdf": pdfs.prompt_injection_pdf,
}


def main() -> None:
    for target in TARGETS:
        target.mkdir(parents=True, exist_ok=True)
        for name, build in FILES.items():
            (target / name).write_bytes(build())
    sys.stdout.write(f"Wrote {len(FILES)} synthetic PDFs to {len(TARGETS)} folders\n")


if __name__ == "__main__":
    main()
