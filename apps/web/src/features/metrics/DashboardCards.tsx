import { CircleCheckBig, ClipboardList, FileCheck2, Hourglass, TriangleAlert } from "lucide-react";

import { dashboardCopy as copy } from "@/content/es";

import type { Dashboard } from "./data";

const CARDS = [
  { key: "active_evaluations", surface: "bg-pastel-periwinkle", Icon: ClipboardList },
  { key: "pending_review", surface: "bg-pastel-sky", Icon: Hourglass },
  { key: "approved", surface: "bg-pastel-mint", Icon: CircleCheckBig },
  { key: "documents_processed", surface: "bg-pastel-lavender", Icon: FileCheck2 },
  { key: "high_priority_findings", surface: "bg-pastel-peach", Icon: TriangleAlert },
] as const;

export function DashboardCards({ counts }: { counts: Dashboard }) {
  return (
    <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5" aria-label="Resumen">
      {CARDS.map(({ key, surface, Icon }) => (
        <li key={key} className={`${surface} flex h-full flex-col gap-3 rounded-3xl p-5`}>
          <span className="bg-surface text-primary flex size-10 items-center justify-center rounded-2xl">
            <Icon className="size-5" aria-hidden="true" />
          </span>
          <span className="text-foreground text-sm font-medium">{copy.cards[key]}</span>
          <span className="text-foreground text-4xl font-light tracking-tight">{counts[key]}</span>
          <span className="text-foreground/75 text-xs leading-relaxed">{copy.hints[key]}</span>
        </li>
      ))}
    </ul>
  );
}
