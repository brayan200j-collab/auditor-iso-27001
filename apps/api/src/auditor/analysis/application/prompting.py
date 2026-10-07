from __future__ import annotations

from collections.abc import Sequence

from auditor.analysis.application.ports import PromptTemplates
from auditor.analysis.domain.evidence import EvidenceCandidate, neutralize
from auditor.checklist.public import ChecklistItem


def _attribute(value: str) -> str:
    return neutralize(value).replace('"', "'").replace("\n", " ")


def evidence_block(candidates: Sequence[EvidenceCandidate]) -> str:
    """Delimited fragments. Document names are replaced by aliases (data minimization)."""
    blocks = []
    for candidate in candidates:
        section = f' seccion="{_attribute(candidate.section)}"' if candidate.section else ""
        blocks.append(
            f'<fragmento id="{candidate.chunk_id}" documento="{candidate.document_alias}" '
            f'pagina="{candidate.page}"{section}>\n{neutralize(candidate.content)}\n</fragmento>'
        )
    return "\n\n".join(blocks)


def user_prompt(
    templates: PromptTemplates, item: ChecklistItem, candidates: Sequence[EvidenceCandidate]
) -> str:
    return templates.evaluation(
        {
            "criterion_code": item.code,
            "criterion_name": item.name,
            "criterion_description": item.description,
            "evaluation_question": item.evaluation_question,
            "expected_evidence": item.expected_evidence,
            "priority": item.priority.value,
            "risk_level": item.risk_level.value,
            "effort": item.effort.value,
            "evidence": evidence_block(candidates),
        }
    )


def correction_note(error: str) -> str:
    return (
        "\n\nTu respuesta anterior no cumplió el formato requerido "
        f"({error[:200]}). Devuelve únicamente el objeto JSON válido."
    )
