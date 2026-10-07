import Link from "next/link";

import { FindingStatusBadge } from "@/components/shared/FindingStatusBadge";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { priorityLabels, resultsCopy as copy, reviewCopy, table } from "@/content/es";

import type { ResultFinding } from "./data";

type ResultsTableProps = { evaluationId: string; findings: ResultFinding[] };

export function ResultsTable({ evaluationId, findings }: ResultsTableProps) {
  return (
    <Table>
      <THead>
        <TR>
          <TH>{reviewCopy.columns.criterion}</TH>
          <TH>{reviewCopy.actions.status}</TH>
          <TH>{reviewCopy.priority}</TH>
          <TH>
            <span className="sr-only">{table.actions}</span>
          </TH>
        </TR>
      </THead>
      <TBody>
        {findings.map((finding) => (
          <TR key={finding.finding_id}>
            <TD className="font-medium">
              {finding.criterion.code} · {finding.criterion.name}
            </TD>
            <TD>
              <FindingStatusBadge status={finding.status} />
            </TD>
            <TD>{priorityLabels[finding.priority]}</TD>
            <TD>
              <Link
                href={`/app/evaluaciones/${evaluationId}/resultados/${finding.finding_id}`}
                className="text-primary underline-offset-4 hover:underline"
                aria-label={copy.detailLabel(finding.criterion.code)}
              >
                {copy.detail}
              </Link>
            </TD>
          </TR>
        ))}
      </TBody>
    </Table>
  );
}
