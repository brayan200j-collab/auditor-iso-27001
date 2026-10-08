import { Card } from "@/components/ui/card";
import { dashboardCopy as copy } from "@/content/es";

import type { Dashboard } from "./data";

const ORDER = [
  "active_evaluations",
  "pending_review",
  "approved",
  "documents_processed",
  "high_priority_findings",
] as const;

export function DashboardCards({ counts }: { counts: Dashboard }) {
  return (
    <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5" aria-label="Resumen">
      {ORDER.map((key) => (
        <li key={key}>
          <Card className="flex h-full flex-col gap-1">
            <span className="text-muted-foreground text-sm">{copy.cards[key]}</span>
            <span className="text-foreground text-3xl font-semibold">{counts[key]}</span>
            <span className="text-muted-foreground text-xs">{copy.hints[key]}</span>
          </Card>
        </li>
      ))}
    </ul>
  );
}
