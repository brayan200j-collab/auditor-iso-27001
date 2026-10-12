import { BadgeCheck, FileText } from "lucide-react";

import { LogoSymbol } from "@/components/shared/BrandMark";
import { FindingStatusBadge } from "@/components/shared/FindingStatusBadge";
import { Badge } from "@/components/ui/badge";
import { landing } from "@/content/es";

const copy = landing.mockup;
// Illustrative example only (labelled on screen); never real company data.
const STATUSES = ["FOUND", "PARTIAL", "NO_DOCUMENTARY_EVIDENCE"] as const;
const TILE_STYLES = [
  "bg-success-soft text-success",
  "bg-warning-soft text-warning",
  "bg-danger-soft text-danger",
];

/** Product mockup for the hero: what an approved self-assessment looks like. */
export function ProductPreview() {
  return (
    <figure className="relative">
      <div
        aria-hidden="true"
        className="bg-pastel-lavender absolute -top-6 -right-4 hidden size-40 rounded-3xl md:block"
      />
      <div
        aria-hidden="true"
        className="bg-pastel-sky absolute -bottom-6 -left-6 hidden size-32 rounded-3xl md:block"
      />
      <div className="border-border/70 bg-surface shadow-card relative rounded-3xl border p-5 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <LogoSymbol className="size-7" />
            <span className="text-foreground text-sm font-semibold">{copy.title}</span>
          </div>
          <Badge tone="success">
            <BadgeCheck className="size-3.5" aria-hidden="true" />
            {copy.reviewed}
          </Badge>
        </div>

        <p className="text-muted-foreground mt-5 text-xs font-medium tracking-wide uppercase">
          {copy.coverageTitle}
        </p>
        <ul className="mt-2 grid grid-cols-3 gap-2">
          {copy.coverage.map((item, index) => (
            <li key={item.label} className={`rounded-2xl p-3 ${TILE_STYLES[index]}`}>
              <span className="block text-2xl font-semibold">{item.value}</span>
              <span className="block text-[11px] leading-tight font-medium">{item.label}</span>
            </li>
          ))}
        </ul>
        <p className="text-muted-foreground mt-1.5 text-right text-[11px]">{copy.of}</p>

        <ul className="divide-border/70 mt-4 divide-y">
          {copy.rows.map((row, index) => (
            <li key={row.code} className="flex flex-wrap items-center justify-between gap-2 py-3">
              <span className="flex flex-col">
                <span className="text-foreground text-sm font-medium">
                  {row.code} · {row.name}
                </span>
                <span className="text-muted-foreground flex items-center gap-1 text-xs">
                  <FileText className="size-3.5" aria-hidden="true" />
                  {row.page}
                </span>
              </span>
              <FindingStatusBadge status={STATUSES[index]} />
            </li>
          ))}
        </ul>
      </div>
      <figcaption className="text-muted-foreground mt-3 text-center text-xs">
        {copy.label}
      </figcaption>
    </figure>
  );
}
