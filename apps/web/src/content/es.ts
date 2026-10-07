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
  whatIs: "¿Qué significa?",
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

export const adminCompanies = {
  title: "Empresas",
  description: "Empresas participantes en el piloto.",
  newTitle: "Nueva empresa",
  editTitle: "Editar empresa",
  name: "Razón social",
  taxId: "NIT",
  taxIdHint: "Solo números, con dígito de verificación opcional. Ejemplo: 900123456-7",
  sector: "Sector",
  city: "Ciudad",
  active: "Empresa activa",
  status: "Estado",
  activeLabel: "Activa",
  inactiveLabel: "Inactiva",
  create: "Crear empresa",
  save: "Guardar cambios",
  saving: "Guardando…",
  created: "La empresa se creó correctamente.",
  updated: "Los cambios se guardaron.",
  empty: "Aún no hay empresas registradas. Crea la primera para invitar a sus usuarios.",
  searchLabel: "Buscar por nombre o NIT",
  search: "Buscar",
  edit: "Editar",
  validation: {
    name: "Escribe la razón social (entre 2 y 200 caracteres).",
    taxId: "El NIT debe tener solo números y, opcionalmente, un dígito de verificación.",
  },
} as const;

export const adminUsers = {
  title: "Usuarios",
  description: "Cuentas de administración, revisión, PYMES y mentoría.",
  newTitle: "Invitar usuario",
  inviteHint:
    "La persona recibirá un correo para definir su contraseña. Nunca compartas contraseñas por otros medios.",
  editTitle: "Editar usuario",
  email: "Correo electrónico",
  fullName: "Nombre completo",
  role: "Rol",
  company: "Empresa",
  companyPlaceholder: "Selecciona una empresa",
  companyHint: "Obligatoria solo para usuarios PYME.",
  status: "Estado",
  activeLabel: "Activo",
  inactiveLabel: "Inactivo",
  create: "Enviar invitación",
  creating: "Enviando…",
  created: "El usuario se creó y se envió la invitación.",
  updated: "Los cambios se guardaron.",
  deactivate: "Desactivar",
  activate: "Activar",
  save: "Guardar cambios",
  edit: "Editar",
  empty: "Aún no hay usuarios con estos filtros.",
  filterRole: "Filtrar por rol",
  searchLabel: "Buscar por nombre o correo",
  search: "Filtrar",
  validation: {
    email: "Escribe un correo electrónico válido.",
    fullName: "Escribe el nombre completo (entre 2 y 200 caracteres).",
    company: "Selecciona la empresa del usuario PYME.",
  },
} as const;

export const table = {
  actions: "Acciones",
  createdAt: "Creado",
  noResults: "Sin resultados.",
  previous: "Anterior",
  next: "Siguiente",
  pagination: "Paginación",
} as const;

export const evaluations = {
  listTitle: "Mis evaluaciones",
  listDescription: "Autoevaluaciones iniciales de tu empresa.",
  adminTitle: "Evaluaciones",
  adminDescription: "Todas las evaluaciones del piloto y su revisor asignado.",
  reviewerTitle: "Evaluaciones asignadas",
  reviewerDescription: "Evaluaciones que te asignaron para revisión humana.",
  newTitle: "Nueva evaluación",
  newDescription:
    "Ponle un nombre que te ayude a reconocerla, por ejemplo «Autoevaluación inicial 2026».",
  titleLabel: "Nombre de la evaluación",
  create: "Crear evaluación",
  creating: "Creando…",
  titleError: "El nombre debe tener entre 3 y 200 caracteres.",
  empty: "Aún no tienes evaluaciones. Crea la primera para cargar tus documentos.",
  emptyReviewer: "No tienes evaluaciones asignadas por ahora.",
  emptyAdmin: "Aún no hay evaluaciones en el piloto.",
  columns: {
    title: "Evaluación",
    company: "Empresa",
    status: "Estado",
    reviewer: "Revisor",
    created: "Creada",
    open: "Abrir",
  },
  statusFilter: "Filtrar por estado",
  filter: "Filtrar",
  unassigned: "Sin asignar",
  assign: "Asignar",
  assignLabel: (title: string) => `Revisor para ${title}`,
  assigned: "Revisor asignado.",
  progressTitle: "Progreso",
  stepStates: {
    DONE: "completado",
    CURRENT: "en curso",
    FAILED: "con error",
    PENDING: "pendiente",
  },
  rejectionTitle: "La evaluación fue rechazada por el revisor",
  rejectionHelp: "Revisa el motivo, carga un PDF actualizado y vuelve a iniciar el análisis.",
  failureTitle: "No pudimos completar el procesamiento",
  failureReasons: {
    EXTRACTION_ERROR:
      "No pudimos leer el contenido del documento. El equipo revisará el caso y podrá reintentar el procesamiento.",
    ANALYSIS_ERROR:
      "El análisis no pudo completarse. El equipo revisará el caso y podrá reintentarlo.",
    INTERRUPTED: "El procesamiento se interrumpió. El equipo podrá reintentarlo.",
    QUOTA_EXCEEDED:
      "Se alcanzó el límite de uso del servicio de análisis. El equipo revisará el caso.",
  },
} as const;

export const consentCopy = {
  title: "Consentimiento",
  description: "Antes de cargar documentos, lee y acepta las condiciones de tratamiento.",
  checkbox: "He leído y acepto las condiciones anteriores.",
  submit: "Aceptar y continuar",
  submitting: "Guardando…",
  required: "Debes aceptar las condiciones para continuar.",
  accepted: "Consentimiento registrado.",
  version: (version: string) => `Versión del texto: ${version}`,
} as const;

export const documentsCopy = {
  title: "Documentos",
  description:
    "Carga tus políticas y procedimientos en PDF con texto seleccionable (máximo 20 MB y 30 páginas por archivo).",
  dropTitle: "Arrastra aquí tu PDF o selecciónalo",
  dropHint:
    "Solo archivos PDF con texto seleccionable. Los documentos escaneados no son compatibles.",
  choose: "Seleccionar PDF",
  uploading: "Cargando y validando…",
  validPdf: "PDF válido",
  pages: (count: number) => `${count} ${count === 1 ? "página" : "páginas"}`,
  textDetected: "Texto detectado",
  empty: "Aún no has cargado documentos.",
  remove: "Eliminar",
  removeLabel: (name: string) => `Eliminar ${name}`,
  removed: "Documento eliminado.",
  size: (bytes: number) => `${(bytes / (1024 * 1024)).toFixed(1)} MB`,
  clientErrors: {
    type: "El archivo debe ser un PDF.",
    size: "El archivo supera el tamaño máximo de 20 MB.",
    empty: "El archivo está vacío.",
  },
  locked: "Los documentos ya no se pueden modificar en este estado de la evaluación.",
  consentFirst: "Acepta el consentimiento para poder cargar documentos.",
} as const;

export const processingCopy = {
  start: "Iniciar análisis",
  starting: "Iniciando…",
  startHint:
    "Cuando hayas cargado todos tus documentos, inicia el análisis. Ya no podrás agregar ni eliminar documentos.",
  live: {
    EXTRACTING: "Extrayendo información de tus documentos…",
    ANALYZING: "Analizando los documentos frente a los 30 criterios del checklist…",
    PENDING_REVIEW:
      "El análisis terminó. Una persona revisará los resultados antes de mostrártelos.",
    FAILED: "El procesamiento no pudo completarse.",
  },
  updated: (time: string) => `Última actualización: ${time}`,
  criteria: (done: number, total: number) => `${done} de ${total} criterios analizados.`,
  retry: "Reintentar procesamiento",
  retrying: "Reintentando…",
  retryHint: "El procesamiento continuará desde el último paso completado.",
} as const;

export const checklistCopy = {
  title: "Checklist",
  description:
    "Checklist propio de 30 criterios alineado con ISO/IEC 27001:2022, con CIS Controls v8.1 y NIST CSF 2.0 como referencias complementarias.",
  versionsTitle: "Versiones del checklist",
  version: (number: number) => `Versión ${number}`,
  statuses: { DRAFT: "Borrador", PUBLISHED: "Publicada" },
  items: (active: number, total: number) => `${active} de ${total} criterios activos`,
  publishedAt: "Publicada",
  createDraft: "Crear borrador desde la versión publicada",
  draftCreated: "Borrador creado.",
  publish: "Publicar versión",
  published: "Versión publicada. Las nuevas evaluaciones la usarán.",
  publishHint:
    "Las versiones publicadas no se pueden modificar. Las evaluaciones en curso conservan la versión con la que iniciaron.",
  view: "Ver criterios",
  edit: "Editar",
  editTitle: (code: string) => `Editar ${code}`,
  saved: "Criterio guardado.",
  readOnly: "Esta versión está publicada y no se puede modificar.",
  columns: {
    criterion: "Criterio",
    priority: "Prioridad",
    references: "Referencias",
    active: "Activo",
  },
  pendingReference: "referencia por confirmar",
  confirmedReference: "referencia confirmada",
  fields: {
    name: "Nombre",
    description: "Descripción",
    question: "Pregunta de evaluación",
    evidence: "Evidencia esperada",
    iso: "Referencia ISO/IEC 27001:2022",
    cis: "Referencia CIS Controls v8.1",
    nist: "Referencia NIST CSF 2.0",
    referenceStatus: "Estado de las referencias",
    keywords: "Palabras clave (separadas por coma)",
    keywordsHint: "Se usan para buscar evidencia en los documentos.",
    priority: "Prioridad",
    risk: "Nivel de riesgo",
    effort: "Esfuerzo estimado",
    active: "Criterio activo",
  },
  yes: "Sí",
  no: "No",
  invalid: "Revisa los campos: hay datos incompletos o no válidos.",
} as const;

export const reviewCopy = {
  summaryTitle: "Resultado del análisis",
  evaluated: (total: number) => `${total} criterios evaluados`,
  found: (count: number) => `Encontrados: ${count}`,
  partial: (count: number) => `Parciales: ${count}`,
  noEvidence: (count: number) => `Sin evidencia: ${count}`,
  errors: (count: number) => `Sin clasificar: ${count}`,
  progress: (reviewed: number, total: number) => `Revisados ${reviewed} de ${total}`,
  queueTitle: "Cola de revisión",
  columns: { criterion: "Criterio", confidence: "Confianza", review: "Revisión" },
  queueHint:
    "Primero aparecen los hallazgos pendientes que requieren atención y los de menor confianza.",
  needsAttention: "Requiere atención",
  aiStatus: "Estado propuesto por la IA",
  unclassified: "Sin clasificar",
  review: "Revisar",
  reviewLabel: (code: string) => `Revisar ${code}`,
  noModelCall: "Sin llamada a la IA",
  noModelCallHelp:
    "No se encontraron fragmentos relevantes, así que el sistema clasificó el criterio sin consultar a la IA.",
  evidenceTitle: "Evidencia",
  noCitations: "Sin citas de evidencia.",
  page: (page: number) => `Página ${page}`,
  unverified: "Cita no verificada: no se encontró en el documento",
  unverifiedHelp: "Esta cita no se mostrará a la empresa.",
  gap: "Brecha",
  recommendation: "Recomendación",
  priority: "Prioridad",
  risk: "Nivel de riesgo",
  effort: "Esfuerzo estimado",
  modelInfo: (provider: string, model: string, version: string, date: string) =>
    `Generado por ${provider} · ${model} · prompts ${version} · ${date}`,
  modelError: "La IA no pudo clasificar este criterio. Edítalo o descártalo.",
  criterionQuestion: "Pregunta de evaluación",
  expectedEvidence: "Evidencia esperada",
  references: "Referencias",
  actions: {
    choose: "Acción de revisión",
    approve: "Aprobar",
    approveHint: "Aprueba el hallazgo tal como lo propuso la IA.",
    edit: "Editar y aprobar",
    discard: "Descartar",
    discardHint: "Indica el motivo del descarte (mínimo 10 caracteres).",
    comment: "Comentario para el registro (opcional)",
    reason: "Motivo",
    status: "Estado",
    saved: "Revisión guardada.",
  },
  history: "Historial de revisión",
  historyActions: {
    APPROVE: "Aprobado",
    EDIT: "Editado y aprobado",
    DISCARD: "Descartado",
  },
  decision: {
    title: "Decisión sobre la evaluación",
    approve: "Aprobar evaluación",
    approveHint:
      "Al aprobar, la empresa verá los resultados revisados y se generará el informe. Esta acción no se puede deshacer.",
    pending: (count: number) =>
      `Faltan ${count} hallazgo(s) por revisar antes de aprobar la evaluación.`,
    reject: "Rechazar evaluación",
    rejectHint: "La empresa verá el motivo y podrá cargar un documento actualizado.",
    reason: "Motivo del rechazo",
    approved: "Evaluación aprobada.",
    rejected: "Evaluación rechazada.",
  },
  backToQueue: "Volver a la cola de revisión",
  locked: "La evaluación ya no está en revisión; los hallazgos no se pueden modificar.",
} as const;
