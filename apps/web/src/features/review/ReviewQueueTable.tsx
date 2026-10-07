import Link from "next/link";

import { FindingStatusBadge, ReviewStatusBadge } from "@/components/shared/FindingStatusBadge";
import { Badge } from "@/components/ui/badge";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { confidence, priorityLabels, reviewCopy, table } from "@/content/es";

import { formatConfidence } from "./ConfidenceValue";
import type { ReviewItem } from "./data";

type ReviewQueueTableProps = { evaluationId: string; items: ReviewItem[] };

export function ReviewQueueTable({ evaluationId, items }: ReviewQueueTableProps) {
  return (
    <Table>
      <THead>
        <TR>
          <TH>{reviewCopy.columns.criterion}</TH>
          <TH>{reviewCopy.aiStatus}</TH>
          <TH>
            <abbr title={confidence.label}>{reviewCopy.columns.confidence}</abbr>
          </TH>
          <TH>{reviewCopy.priority}</TH>
          <TH>{reviewCopy.columns.review}</TH>
          <TH>
            <span className="sr-only">{table.actions}</span>
          </TH>
        </TR>
      </THead>
      <TBody>
        {items.map((item) => {
          const priority = item.review.final?.priority ?? item.ai.preliminary_priority;
          return (
            <TR key={item.finding_id}>
              <TD>
                <p className="font-medium">
                  {item.criterion.code} · {item.criterion.name}
                </p>
                {item.ai.needs_attention && item.review.review_status === "PENDING_REVIEW" ? (
                  <Badge tone="warning" className="mt-1">
                    {reviewCopy.needsAttention}
                  </Badge>
                ) : null}
              </TD>
              <TD>
                <FindingStatusBadge status={item.ai.status} />
              </TD>
              <TD>{formatConfidence(item.ai.confidence)}</TD>
              <TD>{priority ? priorityLabels[priority] : "—"}</TD>
              <TD>
                <ReviewStatusBadge status={item.review.review_status} />
              </TD>
              <TD>
                <Link
                  href={`/app/revision/${evaluationId}/hallazgos/${item.finding_id}`}
                  className="text-primary underline-offset-4 hover:underline"
                  aria-label={reviewCopy.reviewLabel(item.criterion.code)}
                >
                  {reviewCopy.review}
                </Link>
              </TD>
            </TR>
          );
        })}
      </TBody>
    </Table>
  );
}
