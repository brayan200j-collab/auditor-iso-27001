/**
 * Central catalogue of user-facing Spanish text. Components never hardcode copy or show raw enums.
 */

export const brand = {
  name: "Auditor Virtual",
  tagline: "Autoevaluación inicial de seguridad de la información.",
  headline:
    "Obtén una primera lectura clara de tus brechas de seguridad a partir de tus documentos.",
  definition:
    "Auditor Virtual ISO/IEC 27001 con IA es una aplicación web de autoevaluación inicial que analiza documentación empresarial mediante inteligencia artificial y la contrasta con un checklist propio alineado con ISO/IEC 27001:2022, utilizando CIS Controls v8.1 y NIST CSF 2.0 como referencias complementarias. Los resultados generados por la IA son revisados y validados por una persona antes de ser presentados a la empresa.",
} as const;

export const legal = {
  scopeDisclaimer:
    "Este resultado corresponde a una autoevaluación inicial y no constituye una certificación ISO/IEC 27001 ni reemplaza una auditoría realizada por un organismo acreditado.",
  aiProvider:
    "El MVP utiliza un proveedor de inteligencia artificial con nivel gratuito, sujeto a límites de solicitudes y consumo.",
  aiPrivacy:
    "Los documentos se procesan mediante un proveedor externo de inferencia bajo condiciones de tratamiento y privacidad que deben revisarse antes del piloto. El sistema minimiza la información enviada y no incorpora documentos empresariales a los conjuntos de prueba.",
  preliminary: "Resultado preliminar sujeto a revisión",
  draftReference: "referencia por confirmar",
  legalReviewPending: "Borrador: revisar con asesor legal.",
} as const;

export const evaluationStatusLabels = {
  DRAFT: "Borrador",
  RECEIVED: "Recibido",
  EXTRACTING: "Extrayendo información",
  ANALYZING: "Analizando",
  PENDING_REVIEW: "Pendiente de revisión",
  APPROVED: "Aprobado",
  REJECTED: "Rechazado",
  FAILED: "Error",
} as const;

export type EvaluationStatus = keyof typeof evaluationStatusLabels;

export const progressSteps = [
  { key: "RECEIVED", label: "Recibido" },
  { key: "EXTRACTING", label: "Extracción" },
  { key: "ANALYZING", label: "Análisis" },
  { key: "PENDING_REVIEW", label: "Revisión humana" },
  { key: "APPROVED", label: "Aprobado" },
] as const;

export const priorityLabels = {
  CRITICAL: "Crítica",
  HIGH: "Alta",
  MEDIUM: "Media",
  LOW: "Baja",
} as const;

export const riskLabels = { HIGH: "Alto", MEDIUM: "Medio", LOW: "Bajo" } as const;
export const effortLabels = { HIGH: "Alto", MEDIUM: "Medio", LOW: "Bajo" } as const;

export const findingStatusLabels = {
  FOUND: "Encontrado",
  PARTIAL: "Parcial",
  NO_DOCUMENTARY_EVIDENCE: "Sin evidencia documental",
} as const;

export const findingStatusDescriptions = {
  FOUND: "Se encontró evidencia documental relacionada con el criterio.",
  PARTIAL:
    "Se encontró evidencia documental, pero esta resulta insuficiente para cubrir completamente el criterio evaluado.",
  NO_DOCUMENTARY_EVIDENCE:
    "No se encontró evidencia documental suficiente en los documentos aportados.",
} as const;

export const reviewStatusLabels = {
  PENDING_REVIEW: "Pendiente",
  APPROVED: "Aprobado",
  EDITED_APPROVED: "Editado y aprobado",
  DISCARDED: "Descartado",
} as const;

export const roleLabels = {
  ADMIN: "Administrador",
  REVIEWER: "Revisor",
  SME: "PYME",
  MENTOR: "Mentor",
} as const;

export const filterLabels = { ALL: "Todos" } as const;

export const confidence = {
  label: "Nivel de confianza estimado por el modelo para la clasificación del hallazgo",
  help: "Este valor no mide el nivel de seguridad de la empresa. Lo estima el modelo de IA y sirve para ordenar la revisión humana: los hallazgos con menor confianza se revisan primero.",
} as const;

export const coverage = {
  title: "Cobertura documental preliminar",
  withEvidence: (count: number, total: number) =>
    `${count} de ${total} criterios con evidencia documental`,
  partial: (count: number, total: number) => `${count} de ${total} con evidencia parcial`,
  noEvidence: (count: number, total: number) => `${count} de ${total} sin evidencia documental`,
  discarded: (count: number, total: number) => `${count} de ${total} descartados por el revisor`,
} as const;

export const common = {
  loading: "Cargando…",
  noData: "Sin datos aún",
  retry: "Reintentar",
  cancel: "Cancelar",
  save: "Guardar",
  back: "Volver",
  next: "Siguiente",
  previous: "Anterior",
  close: "Cerrar",
  page: (page: number, pages: number) => `Página ${page} de ${pages}`,
  genericError: "Ocurrió un problema. Intenta de nuevo en unos minutos.",
  notFound: "No encontramos lo que buscas o no tienes acceso.",
  skipToContent: "Saltar al contenido principal",
} as const;
