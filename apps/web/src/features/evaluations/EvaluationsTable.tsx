import Link from "next/link";
import type { ReactNode } from "react";

import { EmptyState } from "@/components/shared/EmptyState";
import { EvaluationStatusBadge } from "@/components/shared/EvaluationStatusBadge";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { evaluations, table } from "@/content/es";
import { formatDate } from "@/lib/format";

import type { Evaluation } from "./data";

type EvaluationsTableProps = {
  items: Evaluation[];
  emptyMessage: string;
  hrefFor: (evaluation: Evaluation) => string;
  showCompany?: boolean;
  showReviewer?: boolean;
  /** Optional extra cell per row (e.g. reviewer assignment for administrators). */
  extra?: (evaluation: Evaluation) => ReactNode;
};

export function EvaluationsTable({
  items,
  emptyMessage,
  hrefFor,
  showCompany = false,
  showReviewer = false,
  extra,
}: EvaluationsTableProps) {
  if (items.length === 0) return <EmptyState message={emptyMessage} />;
  return (
    <Table>
      <THead>
        <TR>
          <TH>{evaluations.columns.title}</TH>
          {showCompany ? <TH>{evaluations.columns.company}</TH> : null}
          <TH>{evaluations.columns.status}</TH>
          {showReviewer ? <TH>{evaluations.columns.reviewer}</TH> : null}
          <TH>{evaluations.columns.created}</TH>
          <TH>
            <span className="sr-only">{table.actions}</span>
          </TH>
        </TR>
      </THead>
      <TBody>
        {items.map((evaluation) => (
          <TR key={evaluation.id}>
            <TD className="font-medium">{evaluation.title}</TD>
            {showCompany ? <TD>{evaluation.company_name ?? "—"}</TD> : null}
            <TD>
              <EvaluationStatusBadge status={evaluation.status} />
            </TD>
            {showReviewer ? (
              <TD>
                {extra ? extra(evaluation) : (evaluation.reviewer_name ?? evaluations.unassigned)}
              </TD>
            ) : null}
            <TD>{formatDate(evaluation.created_at)}</TD>
            <TD>
              <Link
                href={hrefFor(evaluation)}
                className="text-primary underline-offset-4 hover:underline"
              >
                {evaluations.columns.open}
                <span className="sr-only"> {evaluation.title}</span>
              </Link>
            </TD>
          </TR>
        ))}
      </TBody>
    </Table>
  );
}
