import { nav } from "@/content/es";

import type { Role } from "./profile";

export type NavItem = { href: string; label: string };

/** Menu entries per role. Presentation only: the API enforces every permission. */
export function navigationFor(role: Role): NavItem[] {
  switch (role) {
    case "SME":
      return [
        { href: "/app", label: nav.home },
        { href: "/app/evaluaciones", label: nav.myEvaluations },
        { href: "/app/evaluaciones/nueva", label: nav.newEvaluation },
      ];
    case "REVIEWER":
      return [
        { href: "/app", label: nav.home },
        { href: "/app/revision", label: nav.assigned },
      ];
    case "ADMIN":
      return [
        { href: "/app", label: nav.home },
        { href: "/app/admin/evaluaciones", label: nav.evaluations },
        { href: "/app/revision", label: nav.assigned },
        { href: "/app/admin/empresas", label: nav.companies },
        { href: "/app/admin/usuarios", label: nav.users },
        { href: "/app/admin/checklist", label: nav.checklist },
        { href: "/app/admin/auditoria", label: nav.auditLogs },
        { href: "/app/metricas", label: nav.metrics },
      ];
    case "MENTOR":
      return [{ href: "/app/metricas", label: nav.metrics }];
  }
}
