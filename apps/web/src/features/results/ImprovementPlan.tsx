import Link from "next/link";

import { FindingStatusBadge } from "@/components/shared/FindingStatusBadge";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { priorityLabels, resultsCopy as copy, reviewCopy } from "@/content/es";

import type { ResultFinding, Results } from "./data";

type ImprovementPlanProps = { evaluationId: string; results: Results };

export function ImprovementPlan({ evaluationId, results }: ImprovementPlanProps) {
  const byId = new Map(results.findings.map((finding) => [finding.finding_id, finding]));
  const phases = results.plan
    .map((phase) => ({
      phase: phase.phase,
      items: phase.finding_ids
        .map((id) => byId.get(id))
        .filter((item): item is ResultFinding => item !== undefined),
    }))
    .filter((phase) => phase.items.length > 0);

  return (
    <Card className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <CardTitle>{copy.planTitle}</CardTitle>
        <CardDescription>{copy.planDescription}</CardDescription>
      </div>
      {phases.length === 0 ? <p className="text-sm">{copy.noGaps}</p> : null}
      {phases.map(({ phase, items }) => (
        <section key={phase} aria-labelledby={`fase-${phase}`} className="flex flex-col gap-2">
          <h3 id={`fase-${phase}`} className="text-foreground font-semibold">
            {copy.phases[phase]}
          </h3>
          <ol className="flex flex-col gap-2">
            {items.map((item) => (
              <li key={item.finding_id} className="border-border rounded-md border p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium">
                    {item.criterion.code} · {item.criterion.name}
                  </span>
                  <FindingStatusBadge status={item.status} />
                  <Badge tone="neutral">
                    {reviewCopy.priority}: {priorityLabels[item.priority]}
                  </Badge>
                </div>
                <p className="mt-2 text-sm">{item.recommendation}</p>
                <Link
                  href={`/app/evaluaciones/${evaluationId}/resultados/${item.finding_id}`}
                  className="text-primary mt-1 inline-block text-sm hover:underline"
                  aria-label={copy.detailLabel(item.criterion.code)}
                >
                  {copy.detail}
                </Link>
              </li>
            ))}
          </ol>
        </section>
      ))}
    </Card>
  );
}
