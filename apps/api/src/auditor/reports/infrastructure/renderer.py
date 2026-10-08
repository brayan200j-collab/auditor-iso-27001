"""Jinja2 (autoescape) → HTML → WeasyPrint → PDF.

The template only receives reviewed results; all document, AI and reviewer text is escaped.
WeasyPrint never fetches remote resources: the URL fetcher refuses everything.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, NoReturn

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from auditor.reports.application.ports import ReportContent
from auditor.review.public import PlanPhase
from auditor.shared.domain.errors import ReportGenerationError

TEMPLATES = Path(__file__).parent / "templates"

STATUS = {
    "FOUND": "Encontrado",
    "PARTIAL": "Parcial",
    "NO_DOCUMENTARY_EVIDENCE": "Sin evidencia documental",
}
STATUS_TEXT = {
    "FOUND": "Se encontró evidencia documental relacionada con el criterio.",
    "PARTIAL": (
        "Se encontró evidencia documental, pero esta resulta insuficiente para cubrir "
        "completamente el criterio evaluado."
    ),
    "NO_DOCUMENTARY_EVIDENCE": (
        "No se encontró evidencia documental suficiente en los documentos aportados."
    ),
}
PRIORITY = {"CRITICAL": "Crítica", "HIGH": "Alta", "MEDIUM": "Media", "LOW": "Baja"}
RISK = {"HIGH": "Alto", "MEDIUM": "Medio", "LOW": "Bajo"}
EFFORT = {"HIGH": "Alto", "MEDIUM": "Medio", "LOW": "Bajo"}
PHASES = {
    PlanPhase.FIRST: "Abordar primero",
    PlanPhase.NEXT: "A continuación",
    PlanPhase.LATER: "Más adelante",
}
MONTHS = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def _refuse_urls(url: str) -> NoReturn:
    raise ValueError(f"external resources are not allowed in reports: {url[:40]}")


def _date(value: Any) -> str:
    return f"{value.day} de {MONTHS[value.month - 1]} de {value.year}"


class WeasyPrintRenderer:
    def __init__(self, timeout_seconds: float = 60.0) -> None:
        self._env = Environment(
            loader=FileSystemLoader(TEMPLATES),
            autoescape=select_autoescape(("html", "j2")),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._env.filters["date"] = _date
        self._timeout = timeout_seconds

    def html(self, content: ReportContent) -> str:
        results = content.results
        return self._env.get_template("report.html.j2").render(
            c=content,
            results=results,
            evaluation=results.evaluation,
            approved_at=results.evaluation.approved_at or results.evaluation.updated_at,
            status=STATUS,
            status_text=STATUS_TEXT,
            priority=PRIORITY,
            risk=RISK,
            effort=EFFORT,
            phases=PHASES,
        )

    def _render_sync(self, content: ReportContent) -> bytes:
        pdf = HTML(string=self.html(content), url_fetcher=_refuse_urls).write_pdf()
        if not pdf:
            raise ReportGenerationError(detail="weasyprint returned no bytes")
        return bytes(pdf)

    async def render(self, content: ReportContent) -> bytes:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._render_sync, content), timeout=self._timeout
            )
        except ReportGenerationError:
            raise
        except Exception as exc:
            raise ReportGenerationError(detail=f"render failed: {type(exc).__name__}") from exc
