import { Card, CardTitle } from "@/components/ui/card";
import { findingStatusLabels, reviewCopy } from "@/content/es";

import type { Review } from "./data";

export function ReviewSummaryCard({ summary }: { summary: Review["summary"] }) {
  const parts = [
    reviewCopy.found(summary.found),
    reviewCopy.partial(summary.partial),
    reviewCopy.noEvidence(summary.no_evidence),
    ...(summary.errors ? [reviewCopy.errors(summary.errors)] : []),
  ];
  const tiles = [
    {
      label: findingStatusLabels.FOUND,
      value: summary.found,
      style: "bg-success-soft text-success",
    },
    {
      label: findingStatusLabels.PARTIAL,
      value: summary.partial,
      style: "bg-warning-soft text-warning",
    },
    {
      label: findingStatusLabels.NO_DOCUMENTARY_EVIDENCE,
      value: summary.no_evidence,
      style: "bg-danger-soft text-danger",
    },
  ];
  return (
    <Card className="flex flex-col gap-5">
      <div className="flex flex-col gap-1">
        <CardTitle>{reviewCopy.summaryTitle}</CardTitle>
        <p className="text-muted-foreground text-sm">
          {reviewCopy.evaluated(summary.total)}: {parts.join(" / ")}
        </p>
      </div>
      <ul className="grid gap-3 sm:grid-cols-3" aria-hidden="true">
        {tiles.map((tile) => (
          <li key={tile.label} className={`rounded-2xl p-4 ${tile.style}`}>
            <span className="block text-3xl font-light">{tile.value}</span>
            <span className="text-sm font-medium">{tile.label}</span>
          </li>
        ))}
      </ul>
      <div className="flex flex-col gap-2">
        <div
          className="bg-surface-muted h-2 overflow-hidden rounded-full"
          role="progressbar"
          aria-label={reviewCopy.progress(summary.reviewed, summary.total)}
          aria-valuemin={0}
          aria-valuemax={summary.total}
          aria-valuenow={summary.reviewed}
        >
          <div
            className="bg-primary h-full rounded-full transition-all"
            style={{ width: `${summary.total ? (summary.reviewed / summary.total) * 100 : 0}%` }}
          />
        </div>
        <p className="text-muted-foreground text-sm" aria-live="polite">
          {reviewCopy.progress(summary.reviewed, summary.total)}
        </p>
      </div>
    </Card>
  );
}
