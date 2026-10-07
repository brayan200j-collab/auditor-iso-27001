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

export const auth = {
  login: {
    title: "Iniciar sesión",
    description: "Ingresa con la cuenta que te asignó el equipo de Auditor Virtual.",
    email: "Correo electrónico",
    password: "Contraseña",
    submit: "Ingresar",
    submitting: "Ingresando…",
    invalidCredentials: "Correo o contraseña incorrectos.",
    forgot: "¿Olvidaste tu contraseña?",
  },
  recovery: {
    title: "Recuperar cuenta",
    description: "Escribe tu correo y te enviaremos instrucciones para restablecer tu contraseña.",
    submit: "Enviar instrucciones",
    submitting: "Enviando…",
    sent: "Si el correo está registrado, recibirás un mensaje con instrucciones para restablecer tu contraseña.",
    backToLogin: "Volver a iniciar sesión",
  },
  reset: {
    title: "Restablecer contraseña",
    password: "Nueva contraseña",
    confirm: "Confirmar contraseña",
    rule: "Mínimo 12 caracteres, con mayúsculas, minúsculas y números.",
    mismatch: "Las contraseñas no coinciden.",
    submit: "Guardar contraseña",
    submitting: "Guardando…",
    success: "Tu contraseña se actualizó. Ya puedes iniciar sesión.",
    expired: "El enlace no es válido o expiró. Solicita uno nuevo.",
  },
  validation: {
    required: "Este campo es obligatorio.",
    email: "Escribe un correo electrónico válido.",
    passwordWeak: "La contraseña no cumple los requisitos.",
  },
  logout: "Cerrar sesión",
  tooManyAttempts: "Demasiados intentos. Espera unos minutos e intenta de nuevo.",
} as const;

export const nav = {
  main: "Navegación principal",
  home: "Inicio",
  myEvaluations: "Mis evaluaciones",
  newEvaluation: "Nueva evaluación",
  assigned: "Evaluaciones asignadas",
  evaluations: "Evaluaciones",
  companies: "Empresas",
  users: "Usuarios",
  checklist: "Checklist",
  auditLogs: "Registro de auditoría",
  metrics: "Métricas",
  signedInAs: (name: string, role: string) => `${name} · ${role}`,
} as const;

export const publicPages = {
  login: "Iniciar sesión",
  privacy: "Privacidad y condiciones",
  howItWorksTitle: "Cómo funciona",
  steps: [
    {
      title: "Carga tu documentación",
      text: "Sube en PDF tus políticas y procedimientos de seguridad (hasta 30 páginas por archivo).",
    },
    {
      title: "Análisis con IA",
      text: "El sistema busca evidencia en tus documentos y la contrasta con un checklist propio de 30 criterios.",
    },
    {
      title: "Revisión humana",
      text: "Una persona revisa, ajusta y valida cada hallazgo antes de que lo veas.",
    },
    {
      title: "Informe y plan inicial",
      text: "Recibes la cobertura documental preliminar, las brechas priorizadas y un plan inicial de mejora en PDF.",
    },
  ],
  referencesTitle: "Marco de referencia",
  references:
    "Checklist propio alineado con ISO/IEC 27001:2022 como marco principal, con CIS Controls v8.1 (IG1) y NIST CSF 2.0 como referencias complementarias.",
  limitsTitle: "Lo que esta herramienta no hace",
  limits: [
    "No certifica ISO/IEC 27001.",
    "No reemplaza a un auditor acreditado.",
    "No es una auditoría automática: cada resultado es revisado por una persona.",
  ],
  academic:
    "Proyecto académico de la Electiva Emprendimiento en TIC, Universidad Santiago de Cali, para PYMES del Valle del Cauca.",
} as const;

export const privacyPage = {
  title: "Privacidad y condiciones de uso",
  draftNotice: "Borrador: revisar con asesor legal antes del piloto.",
  sections: [
    {
      title: "Responsable y finalidad",
      paragraphs: [
        "Auditor Virtual trata la información que las empresas cargan con la única finalidad de realizar una autoevaluación inicial de seguridad de la información y entregar un informe preliminar revisado por una persona.",
        "El tratamiento de datos personales se rige por la Ley 1581 de 2012 y sus normas reglamentarias. Los titulares pueden conocer, actualizar, rectificar y solicitar la supresión de sus datos, y revocar la autorización otorgada.",
      ],
    },
    {
      title: "Uso de inteligencia artificial",
      paragraphs: [
        "Los documentos se procesan mediante un proveedor externo de inferencia bajo condiciones de tratamiento y privacidad que deben revisarse antes del piloto. El sistema minimiza la información enviada y no incorpora documentos empresariales a los conjuntos de prueba.",
        "El MVP utiliza un proveedor de inteligencia artificial con nivel gratuito, sujeto a límites de solicitudes y consumo.",
        "Al proveedor solo se envían fragmentos relevantes de los documentos, sin el nombre de la empresa ni datos de los usuarios.",
      ],
    },
    {
      title: "Conservación y eliminación",
      paragraphs: [
        "Los PDF originales y sus fragmentos se eliminan a los 90 días de aprobada la evaluación. Se conservan los hallazgos finales y el informe.",
        "Puedes eliminar un documento antes de iniciar el análisis. Toda eliminación queda registrada en el registro de auditoría.",
      ],
    },
    {
      title: "Alcance del resultado",
      paragraphs: [
        "Este resultado corresponde a una autoevaluación inicial y no constituye una certificación ISO/IEC 27001 ni reemplaza una auditoría realizada por un organismo acreditado.",
      ],
    },
    {
      title: "Seguridad",
      paragraphs: [
        "Los documentos se almacenan de forma privada, se accede a ellos solo tras verificar los permisos de cada usuario y las descargas usan enlaces temporales.",
      ],
    },
  ],
} as const;
