"""Versioned consent shown before any document is uploaded (CLAUDE.md sections 1 and 9).

Changing the text requires a new version; each acceptance stores the version and a hash of the
exact text that was shown.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

CURRENT_CONSENT_VERSION = "2026-10-v1"

CONSENT_TEXT = "\n".join(
    [
        "Autorizo a Auditor Virtual a procesar los documentos que cargue para esta evaluación con "
        "la única finalidad de realizar una autoevaluación inicial de seguridad de la información.",
        "Entiendo que los documentos se procesan mediante un proveedor externo de inferencia bajo "
        "condiciones de tratamiento y privacidad que deben revisarse antes del piloto. El sistema "
        "minimiza la información enviada y no incorpora documentos empresariales a los conjuntos "
        "de prueba.",
        "Entiendo que el MVP utiliza un proveedor de inteligencia artificial con nivel gratuito, "
        "sujeto a límites de solicitudes y consumo.",
        "Entiendo que los resultados son revisados por una persona antes de mostrármelos y que "
        "este resultado corresponde a una autoevaluación inicial y no constituye una "
        "certificación ISO/IEC 27001 ni reemplaza una auditoría realizada por un organismo "
        "acreditado.",
        "Entiendo que los PDF originales y sus fragmentos se eliminan a los 90 días de aprobada "
        "la evaluación, que puedo eliminar un documento antes de iniciar el análisis y que puedo "
        "ejercer mis derechos sobre datos personales según la Ley 1581 de 2012.",
        "Declaro que tengo autorización de mi empresa para compartir estos documentos.",
    ]
)


@dataclass(frozen=True, slots=True)
class ConsentText:
    version: str
    text: str

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()


CURRENT_CONSENT = ConsentText(version=CURRENT_CONSENT_VERSION, text=CONSENT_TEXT)
