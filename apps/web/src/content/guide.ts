/**
 * Plain-language guide for SMEs without security background: what the 30 criteria mean, which
 * documents help and how to read the results. Own wording; no text of the standards is copied.
 * Re-exported by `es.ts` (central copy module) so the wording rules apply to it too.
 */

export type CriterionGuide = {
  code: string;
  title: string;
  plain: string;
  lookFor: string;
  documents: string[];
};

export type CriteriaGroup = {
  id: string;
  title: string;
  intro: string;
  criteria: CriterionGuide[];
};

export const criteriaGroups: CriteriaGroup[] = [
  {
    id: "direccion",
    title: "Dirección y organización",
    intro: "Cómo la empresa decide, organiza y revisa su seguridad.",
    criteria: [
      {
        code: "ISO-01",
        title: "Política de seguridad",
        plain:
          "Un documento aprobado por la gerencia que dice cómo la empresa protege su información.",
        lookFor:
          "Una política escrita, quién la aprobó, desde cuándo rige y cada cuánto se revisa.",
        documents: ["Política de seguridad de la información", "Manual del sistema de gestión"],
      },
      {
        code: "ISO-02",
        title: "Responsables de la seguridad",
        plain: "Saber quién se encarga de cada tarea de seguridad y quién responde si algo falla.",
        lookFor: "Cargos o personas con funciones de seguridad asignadas por escrito.",
        documents: [
          "Manual de funciones",
          "Organigrama con responsabilidades",
          "Acta de nombramiento",
        ],
      },
      {
        code: "ISO-03",
        title: "Qué se protege y dónde",
        plain: "Definir qué áreas, sedes, procesos y sistemas cubre la seguridad de la empresa.",
        lookFor: "La descripción del alcance: procesos, sedes y sistemas incluidos o excluidos.",
        documents: ["Documento de alcance", "Política de seguridad", "Descripción de procesos"],
      },
      {
        code: "ISO-06",
        title: "Metas de seguridad",
        plain:
          "Objetivos concretos (por ejemplo, reducir incidentes) y cómo se mide si se cumplen.",
        lookFor: "Objetivos con indicadores, responsables y frecuencia de seguimiento.",
        documents: ["Plan de objetivos", "Tablero de indicadores", "Informe de gestión"],
      },
      {
        code: "ISO-29",
        title: "Revisión interna y de la gerencia",
        plain: "Revisar de forma periódica si las medidas funcionan y que la gerencia lo conozca.",
        lookFor:
          "Auditorías internas planificadas e informes o actas de revisión por la dirección.",
        documents: ["Programa e informe de auditoría interna", "Acta de revisión por la dirección"],
      },
      {
        code: "ISO-30",
        title: "Mejora continua",
        plain: "Corregir lo que falla y aprender de los errores para no repetirlos.",
        lookFor: "Registro de problemas encontrados, sus causas y las acciones para corregirlos.",
        documents: ["Registro de acciones correctivas", "Plan de mejora"],
      },
    ],
  },
  {
    id: "riesgos",
    title: "Riesgos",
    intro: "Pensar qué podría salir mal y decidir qué hacer al respecto.",
    criteria: [
      {
        code: "ISO-04",
        title: "Identificar riesgos",
        plain:
          "Hacer una lista de lo que podría afectar la información (robo, daños, errores) y qué tan grave sería.",
        lookFor: "Un método para valorar riesgos y una matriz o listado de riesgos actualizado.",
        documents: ["Metodología de riesgos", "Matriz de riesgos"],
      },
      {
        code: "ISO-05",
        title: "Plan para los riesgos",
        plain: "Decidir qué hacer con cada riesgo importante, quién lo hará y para cuándo.",
        lookFor: "Acciones por riesgo, responsables, fechas y aprobación de los riesgos aceptados.",
        documents: ["Plan de tratamiento de riesgos", "Matriz de riesgos con acciones"],
      },
    ],
  },
  {
    id: "personas",
    title: "Personas",
    intro: "Las personas son la primera línea de protección.",
    criteria: [
      {
        code: "ISO-12",
        title: "Seguridad al contratar y al salir",
        plain: "Reglas de seguridad antes, durante y al terminar el trabajo de cada persona.",
        lookFor: "Acuerdos de confidencialidad, verificaciones al contratar y pasos al retirarse.",
        documents: ["Reglamento interno", "Acuerdo de confidencialidad", "Procedimiento de retiro"],
      },
      {
        code: "ISO-13",
        title: "Capacitación en seguridad",
        plain: "Enseñar al equipo a reconocer engaños, proteger datos y reportar problemas.",
        lookFor: "Un plan de capacitación, temas, frecuencia y registros de asistencia.",
        documents: [
          "Plan de capacitación",
          "Registro de asistencia",
          "Material de sensibilización",
        ],
      },
      {
        code: "ISO-15",
        title: "Celulares y trabajo en casa",
        plain: "Reglas para usar equipos móviles y trabajar fuera de la oficina de forma segura.",
        lookFor: "Una política de teletrabajo o de uso de dispositivos con reglas claras.",
        documents: ["Política de teletrabajo", "Política de uso de dispositivos"],
      },
    ],
  },
  {
    id: "informacion",
    title: "Información y activos",
    intro: "Saber qué información y equipos tiene la empresa y cómo se cuidan.",
    criteria: [
      {
        code: "ISO-07",
        title: "Inventario de activos",
        plain:
          "Una lista de los equipos, programas e información importantes y quién es su responsable.",
        lookFor: "Un inventario con responsables y un procedimiento para mantenerlo al día.",
        documents: [
          "Inventario de activos (exportado a PDF)",
          "Procedimiento de gestión de activos",
        ],
      },
      {
        code: "ISO-08",
        title: "Clasificar la información",
        plain:
          "Marcar la información según qué tan sensible es (pública, interna, confidencial) y cómo se maneja.",
        lookFor: "Niveles de clasificación y reglas de etiquetado, envío y destrucción.",
        documents: ["Política de clasificación de la información", "Guía de manejo de documentos"],
      },
      {
        code: "ISO-17",
        title: "Cifrado y protección de datos",
        plain:
          "Proteger los datos para que solo los lean quienes deben, por ejemplo cifrando discos o archivos.",
        lookFor: "Cuándo se cifra la información y cómo se protegen las claves.",
        documents: ["Política de cifrado", "Política de protección de datos"],
      },
      {
        code: "ISO-28",
        title: "Leyes y datos personales",
        plain:
          "Cumplir las leyes que aplican, como la Ley 1581 de 2012 de protección de datos personales en Colombia.",
        lookFor:
          "Política de tratamiento de datos, autorizaciones y obligaciones legales o contractuales.",
        documents: ["Política de tratamiento de datos personales", "Matriz de requisitos legales"],
      },
    ],
  },
  {
    id: "accesos",
    title: "Accesos",
    intro: "Que cada persona entre solo a lo que necesita.",
    criteria: [
      {
        code: "ISO-09",
        title: "Control de acceso",
        plain: "Cada persona accede solo a la información y sistemas que necesita para su trabajo.",
        lookFor: "Reglas de acceso por cargo y el principio de dar el mínimo permiso necesario.",
        documents: ["Política de control de acceso", "Matriz de perfiles y permisos"],
      },
      {
        code: "ISO-10",
        title: "Contraseñas y doble verificación",
        plain:
          "Contraseñas seguras y, cuando sea posible, un segundo paso para entrar (como un código en el celular).",
        lookFor: "Reglas de contraseñas y uso de autenticación de doble factor (MFA).",
        documents: ["Política de contraseñas", "Procedimiento de autenticación"],
      },
      {
        code: "ISO-11",
        title: "Altas, bajas y revisión de accesos",
        plain:
          "Dar acceso a quien entra, quitarlo a quien sale y revisar periódicamente quién tiene qué.",
        lookFor: "Pasos para crear y retirar usuarios y revisiones periódicas de permisos.",
        documents: ["Procedimiento de gestión de usuarios", "Registro de revisión de accesos"],
      },
    ],
  },
  {
    id: "operacion",
    title: "Tecnología y operación",
    intro: "El día a día de los equipos, programas y redes.",
    criteria: [
      {
        code: "ISO-16",
        title: "Copias de seguridad",
        plain:
          "Guardar copias de la información para recuperarla si se pierde o se daña, y probar que funcionan.",
        lookFor: "Qué se respalda, cada cuánto, dónde se guarda y pruebas de restauración.",
        documents: ["Procedimiento de copias de respaldo", "Registro de pruebas de restauración"],
      },
      {
        code: "ISO-18",
        title: "Protección contra virus",
        plain:
          "Usar antivirus o soluciones similares y mantenerlos actualizados en todos los equipos.",
        lookFor: "Herramientas de protección, su actualización y qué hacer si se detecta algo.",
        documents: ["Política de protección contra malware", "Procedimiento de TI"],
      },
      {
        code: "ISO-19",
        title: "Actualizaciones y vulnerabilidades",
        plain: "Instalar a tiempo las actualizaciones de seguridad y corregir fallas conocidas.",
        lookFor: "Frecuencia de actualizaciones, revisión de vulnerabilidades y responsables.",
        documents: [
          "Procedimiento de gestión de parches",
          "Informe de escaneo de vulnerabilidades",
        ],
      },
      {
        code: "ISO-20",
        title: "Configuración segura",
        plain:
          "Configurar equipos y servidores de forma segura, por ejemplo cambiando claves de fábrica.",
        lookFor:
          "Configuraciones base, desactivación de lo innecesario y control de cambios en ellas.",
        documents: ["Guía de configuración segura", "Procedimiento de instalación de equipos"],
      },
      {
        code: "ISO-21",
        title: "Seguridad de la red",
        plain:
          "Proteger la red e internet de la empresa: firewall, wifi seguro y separación de redes.",
        lookFor: "Medidas de protección de la red, acceso remoto seguro y redes separadas.",
        documents: ["Política de seguridad de redes", "Diagrama o descripción de red"],
      },
      {
        code: "ISO-22",
        title: "Registros y monitoreo",
        plain:
          "Guardar registros de lo que pasa en los sistemas y revisarlos para detectar problemas.",
        lookFor: "Qué eventos se registran, cuánto tiempo se guardan y quién los revisa.",
        documents: ["Procedimiento de registros (logs)", "Política de monitoreo"],
      },
      {
        code: "ISO-27",
        title: "Cambios y desarrollo seguro",
        plain:
          "Aprobar y probar los cambios en sistemas antes de aplicarlos y programar de forma segura.",
        lookFor:
          "Un proceso de solicitud, prueba y aprobación de cambios y buenas prácticas de desarrollo.",
        documents: ["Procedimiento de gestión de cambios", "Guía de desarrollo seguro"],
      },
    ],
  },
  {
    id: "instalaciones",
    title: "Instalaciones",
    intro: "La protección física de oficinas y equipos.",
    criteria: [
      {
        code: "ISO-14",
        title: "Seguridad física",
        plain:
          "Controlar quién entra a las oficinas y proteger los equipos de robos, daños o fallas eléctricas.",
        lookFor:
          "Control de ingreso, áreas restringidas, protección de equipos y borrado seguro al desecharlos.",
        documents: ["Reglamento de acceso a instalaciones", "Procedimiento de seguridad física"],
      },
    ],
  },
  {
    id: "continuidad",
    title: "Incidentes y continuidad",
    intro: "Cómo reaccionar cuando algo sale mal y seguir operando.",
    criteria: [
      {
        code: "ISO-23",
        title: "Atención de incidentes",
        plain:
          "Saber cómo reportar y atender un problema de seguridad, como un virus o una fuga de datos.",
        lookFor: "Canal de reporte, pasos de respuesta, responsables y registro de incidentes.",
        documents: ["Procedimiento de gestión de incidentes", "Registro de incidentes"],
      },
      {
        code: "ISO-24",
        title: "Continuidad del negocio",
        plain: "Un plan para seguir trabajando o recuperarse rápido ante una crisis o un desastre.",
        lookFor: "Plan de continuidad, tiempos de recuperación y pruebas del plan.",
        documents: ["Plan de continuidad del negocio", "Plan de recuperación ante desastres"],
      },
    ],
  },
  {
    id: "terceros",
    title: "Proveedores y nube",
    intro: "Cuidar la información que manejan terceros.",
    criteria: [
      {
        code: "ISO-25",
        title: "Proveedores",
        plain:
          "Exigir a los proveedores que también protejan la información que reciben de la empresa.",
        lookFor: "Cláusulas de seguridad y confidencialidad y evaluación de proveedores críticos.",
        documents: [
          "Contratos o acuerdos con proveedores",
          "Procedimiento de evaluación de proveedores",
        ],
      },
      {
        code: "ISO-26",
        title: "Servicios en la nube",
        plain:
          "Usar servicios en la nube (correo, almacenamiento, programas) de forma segura y controlada.",
        lookFor:
          "Inventario de servicios en la nube, responsables, respaldo y condiciones del proveedor.",
        documents: ["Política de uso de servicios en la nube", "Contratos de servicios en la nube"],
      },
    ],
  },
];

export const documentGuide = {
  title: "¿Qué documentos debo subir?",
  intro:
    "Sube los documentos que describan cómo trabaja tu empresa en temas de seguridad. No necesitas tenerlos todos: cada documento ayuda a cubrir varios criterios.",
  types: [
    {
      name: "Política de seguridad de la información",
      covers: ["ISO-01", "ISO-02", "ISO-03", "ISO-06"],
    },
    { name: "Matriz o metodología de riesgos", covers: ["ISO-04", "ISO-05"] },
    { name: "Inventario de activos", covers: ["ISO-07", "ISO-08"] },
    { name: "Política de control de acceso y contraseñas", covers: ["ISO-09", "ISO-10", "ISO-11"] },
    {
      name: "Reglamento interno, manual de funciones o plan de capacitación",
      covers: ["ISO-02", "ISO-12", "ISO-13"],
    },
    { name: "Política de teletrabajo o uso de dispositivos", covers: ["ISO-15"] },
    { name: "Procedimiento de copias de respaldo", covers: ["ISO-16"] },
    {
      name: "Procedimientos de TI (antivirus, actualizaciones, redes, registros)",
      covers: ["ISO-18", "ISO-19", "ISO-20", "ISO-21", "ISO-22"],
    },
    { name: "Procedimiento de gestión de incidentes", covers: ["ISO-23"] },
    { name: "Plan de continuidad del negocio", covers: ["ISO-24"] },
    { name: "Contratos con proveedores y servicios en la nube", covers: ["ISO-25", "ISO-26"] },
    { name: "Procedimiento de gestión de cambios o desarrollo", covers: ["ISO-27"] },
    { name: "Política de tratamiento de datos personales", covers: ["ISO-17", "ISO-28"] },
    {
      name: "Informes de auditoría interna, actas de gerencia y planes de mejora",
      covers: ["ISO-29", "ISO-30"],
    },
    { name: "Reglamento de acceso a instalaciones", covers: ["ISO-14"] },
  ],
  coversLabel: "Ayuda con:",
  tipsTitle: "Consejos para tus archivos",
  tips: [
    "Sube PDF con texto seleccionable. Los documentos escaneados (fotos de papel) no se pueden leer.",
    "Máximo 30 páginas y 20 MB por archivo, y hasta 5 archivos por evaluación. Si un manual es más largo, divídelo por temas.",
    "Prefiere versiones aprobadas y vigentes de tus documentos.",
    "No subas documentos con datos personales innecesarios (nóminas, cédulas, historias clínicas): no aportan evidencia.",
    "Si no tienes un documento, no pasa nada: el resultado te dirá qué falta y te dará una recomendación para empezar.",
  ],
  more: "Ver la guía completa",
} as const;

export const guide = {
  title: "Guía de uso",
  description:
    "Todo lo que necesitas para hacer tu autoevaluación inicial, aunque nunca hayas trabajado con seguridad de la información.",
  print: "Imprimir o guardar en PDF",
  toc: "Contenido",
  sections: {
    iso: "¿Qué es ISO/IEC 27001?",
    app: "¿Qué hace Auditor Virtual?",
    steps: "Paso a paso",
    documents: "Qué documentos subir",
    criteria: "Los 30 criterios explicados",
    results: "Cómo leer tus resultados",
    faq: "Preguntas frecuentes",
    glossary: "Glosario",
  },
  iso: [
    "ISO/IEC 27001 es una norma internacional que describe cómo una organización puede proteger su información de forma ordenada: identificar riesgos, decidir medidas, asignar responsables y revisar que todo funcione.",
    "Las empresas que quieren una certificación pasan por una auditoría de un organismo acreditado. Auditor Virtual no certifica: te da una primera lectura de qué tan documentada está tu seguridad, para que sepas por dónde empezar.",
    "Para hacerlo fácil, agrupamos los temas más importantes en 30 criterios con nuestras propias palabras, alineados con ISO/IEC 27001:2022 y con CIS Controls v8.1 y NIST CSF 2.0 como referencias complementarias.",
  ],
  app: "La plataforma lee los documentos que subes, busca en ellos evidencia de cada uno de los 30 criterios y te muestra, después de la revisión de una persona, qué temas están bien documentados, cuáles a medias y cuáles faltan, con recomendaciones priorizadas.",
  steps: [
    { title: "Inicia sesión", text: "Usa la cuenta que te envió el equipo de Auditor Virtual." },
    {
      title: "Crea una evaluación",
      text: "En «Nueva evaluación», escribe un nombre, por ejemplo «Autoevaluación 2026».",
    },
    {
      title: "Acepta el consentimiento",
      text: "Lee cómo se tratan tus documentos y acepta para continuar.",
    },
    {
      title: "Sube tus PDF",
      text: "Elige los documentos de la sección «Qué documentos subir». Verás si cada archivo es válido.",
    },
    {
      title: "Inicia el análisis",
      text: "Pulsa «Iniciar análisis». Tarda unos minutos; puedes cerrar la página y volver luego.",
    },
    {
      title: "Espera la revisión humana",
      text: "Una persona revisa cada resultado antes de mostrártelo. Te aparecerá «Pendiente de revisión».",
    },
    {
      title: "Consulta tus resultados",
      text: "Cuando esté aprobada, entra a «Ver resultados aprobados», revisa el plan y descarga el informe en PDF.",
    },
    {
      title: "Cuéntanos tu experiencia",
      text: "Responde la encuesta de dos minutos; nos ayuda a mejorar.",
    },
  ],
  results: {
    intro: "Cada criterio recibe uno de tres estados según lo que se encontró en tus documentos:",
    statuses: [
      {
        status: "FOUND",
        meaning: "Tus documentos describen este tema. Mantén la evidencia actualizada.",
      },
      {
        status: "PARTIAL",
        meaning: "El tema aparece, pero falta información o formalizarlo. Revisa la recomendación.",
      },
      {
        status: "NO_DOCUMENTARY_EVIDENCE",
        meaning:
          "No lo encontramos en los documentos que subiste. No significa que no lo hagas: significa que no está escrito o no subiste ese documento.",
      },
    ],
    levelsTitle: "Prioridad, riesgo y esfuerzo",
    levels: [
      "Prioridad: qué tan pronto conviene atender la brecha (Crítica, Alta, Media o Baja).",
      "Nivel de riesgo: qué tan grave podría ser para tu empresa si no se atiende.",
      "Esfuerzo estimado: cuánto trabajo aproximado requiere (Bajo, Medio o Alto).",
    ],
    planTitle: "Plan inicial de mejora",
    plan: "Las brechas se ordenan en tres fases: «Abordar primero» (prioridad crítica o alta), «A continuación» (media) y «Más adelante» (baja). Empieza por la primera fase.",
    coverage:
      "La cobertura documental preliminar se muestra siempre en conteos, por ejemplo «14 de 30 criterios con evidencia documental». Es una lectura inicial, no una calificación.",
  },
  faq: [
    {
      q: "¿Necesito saber de ISO/IEC 27001 para usar la plataforma?",
      a: "No. Esta guía explica cada criterio con ejemplos. Solo necesitas los documentos de tu empresa.",
    },
    {
      q: "¿Qué pasa si no tengo ningún documento de seguridad?",
      a: "Puedes subir lo que tengas (reglamento interno, manuales, contratos). El resultado mostrará qué falta y te dará recomendaciones para empezar.",
    },
    {
      q: "¿La plataforma me certifica en ISO/IEC 27001?",
      a: "No. Es una autoevaluación inicial que no constituye una certificación ni reemplaza una auditoría de un organismo acreditado.",
    },
    {
      q: "¿Quién ve mis documentos?",
      a: "Solo tu empresa, el revisor asignado y el administrador del piloto. Cada consulta queda registrada y los PDF se eliminan 90 días después de aprobada la evaluación.",
    },
    {
      q: "¿Por qué tengo que esperar la revisión humana?",
      a: "Porque la IA puede equivocarse. Una persona valida cada hallazgo para que los resultados sean confiables.",
    },
    {
      q: "Mi PDF fue rechazado, ¿qué hago?",
      a: "Lee el motivo en pantalla. Lo más común es que esté escaneado, protegido con contraseña o tenga más de 30 páginas. Exporta el documento original a PDF o divídelo.",
    },
  ],
  glossary: [
    {
      term: "Activo",
      definition:
        "Todo lo que tiene valor para la empresa: información, equipos, programas, personas.",
    },
    {
      term: "Brecha",
      definition: "La diferencia entre lo que pide un criterio y lo que muestran tus documentos.",
    },
    {
      term: "Evidencia documental",
      definition: "Una parte de tus documentos que demuestra que un tema está definido.",
    },
    {
      term: "Riesgo",
      definition: "Algo que podría pasar y afectar tu información, junto con qué tan grave sería.",
    },
    {
      term: "Control",
      definition: "Una medida para reducir un riesgo, por ejemplo hacer copias de respaldo.",
    },
    {
      term: "Incidente",
      definition:
        "Un evento que afecta o pudo afectar la seguridad, como un virus o una fuga de datos.",
    },
    {
      term: "MFA",
      definition:
        "Autenticación de doble factor: un segundo paso además de la contraseña para entrar.",
    },
  ],
  criterionHelp: {
    title: "¿Qué significa este criterio?",
    lookFor: "Qué buscamos en tus documentos",
    documents: "Documentos que te pueden ayudar",
  },
  readResults: "Cómo leer tus resultados",
  firstSteps: {
    title: "Primeros pasos",
    text: "¿Es tu primera vez? Revisa qué documentos subir y cómo leer tus resultados en la guía de uso.",
    cta: "Abrir la guía de uso",
  },
} as const;
