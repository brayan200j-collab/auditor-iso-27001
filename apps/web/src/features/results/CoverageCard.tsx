import { Card, CardTitle } from "@/components/ui/card";
import { resultsCopy as copy } from "@/content/es";

import type { Results } from "./data";

/** Coverage as counts only: never a percentage. */
export function CoverageCard({ coverage }: { coverage: Results["coverage"] }) {
  const { total } = coverage;
  const lines = [
    {
      key: "found",
      value: coverage.found,
      text: copy.coverageFound(coverage.found, total),
      tone: "bg-success-soft text-success",
    },
    {
      key: "partial",
      value: coverage.partial,
      text: copy.coveragePartial(coverage.partial, total),
      tone: "bg-warning-soft text-warning",
    },
    {
      key: "none",
      value: coverage.no_evidence,
      text: copy.coverageNone(coverage.no_evidence, total),
      tone: "bg-danger-soft text-danger",
    },
    ...(coverage.discarded
      ? [
          {
            key: "discarded",
            value: coverage.discarded,
            text: copy.coverageDiscarded(coverage.discarded, total),
            tone: "bg-neutral-soft text-neutral",
          },
        ]
      : []),
  ];
  return (
    <Card className="flex flex-col gap-4">
      <CardTitle>{copy.coverageTitle}</CardTitle>
      <ul
        className={`grid gap-3 sm:grid-cols-2 ${lines.length > 3 ? "lg:grid-cols-4" : "lg:grid-cols-3"}`}
      >
        {lines.map((line) => (
          <li key={line.key} className={`flex flex-col gap-1 rounded-2xl p-4 ${line.tone}`}>
            <span className="text-3xl font-light" aria-hidden="true">
              {line.value}
            </span>
            <span className="text-sm font-medium">{line.text}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
