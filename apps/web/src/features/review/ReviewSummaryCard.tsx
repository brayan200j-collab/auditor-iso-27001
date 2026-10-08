import { Card, CardTitle } from "@/components/ui/card";
import { reviewCopy } from "@/content/es";

import type { Review } from "./data";

export function ReviewSummaryCard({ summary }: { summary: Review["summary"] }) {
  const parts = [
    reviewCopy.found(summary.found),
    reviewCopy.partial(summary.partial),
    reviewCopy.noEvidence(summary.no_evidence),
    ...(summary.errors ? [reviewCopy.errors(summary.errors)] : []),
  ];
  return (
    <Card className="flex flex-col gap-2">
      <CardTitle>{reviewCopy.summaryTitle}</CardTitle>
      <p className="text-foreground text-lg font-semibold">
        {reviewCopy.evaluated(summary.total)}: {parts.join(" / ")}
      </p>
      <p className="text-muted-foreground text-sm" aria-live="polite">
        {reviewCopy.progress(summary.reviewed, summary.total)}
      </p>
    </Card>
  );
}
