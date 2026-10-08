import { Card, CardTitle } from "@/components/ui/card";
import { resultsCopy as copy } from "@/content/es";

import type { Results } from "./data";

/** Coverage as counts only: never a percentage. */
export function CoverageCard({ coverage }: { coverage: Results["coverage"] }) {
  const { total } = coverage;
  const lines = [
    { key: "found", text: copy.coverageFound(coverage.found, total), tone: "bg-success" },
    { key: "partial", text: copy.coveragePartial(coverage.partial, total), tone: "bg-warning" },
    { key: "none", text: copy.coverageNone(coverage.no_evidence, total), tone: "bg-danger" },
    ...(coverage.discarded
      ? [
          {
            key: "discarded",
            text: copy.coverageDiscarded(coverage.discarded, total),
            tone: "bg-muted-foreground",
          },
        ]
      : []),
  ];
  return (
    <Card className="flex flex-col gap-3">
      <CardTitle>{copy.coverageTitle}</CardTitle>
      <ul className="flex flex-col gap-2">
        {lines.map((line) => (
          <li key={line.key} className="text-foreground flex items-center gap-3 text-base">
            <span className={`size-3 shrink-0 rounded-full ${line.tone}`} aria-hidden="true" />
            {line.text}
          </li>
        ))}
      </ul>
    </Card>
  );
}
