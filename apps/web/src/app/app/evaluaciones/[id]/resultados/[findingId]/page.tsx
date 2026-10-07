import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { FindingStatusBadge } from "@/components/shared/FindingStatusBadge";
import { PageHeader } from "@/components/shared/PageHeader";
import { Alert } from "@/components/ui/alert";
import { Card, CardTitle } from "@/components/ui/card";
import {
  effortLabels,
  findingStatusDescriptions,
  legal,
  priorityLabels,
  resultsCopy as copy,
  reviewCopy,
  riskLabels,
} from "@/content/es";
import { ReferenceList } from "@/features/admin-checklist";
import { getResults } from "@/features/results";
import { EvidenceList } from "@/features/review";
import { requireRole } from "@/lib/guards";

export const metadata: Metadata = { title: copy.title };

export default async function ResultFindingPage({
  params,
}: PageProps<"/app/evaluaciones/[id]/resultados/[findingId]">) {
  await requireRole("SME", "REVIEWER", "ADMIN");
  const { id, findingId } = await params;
  const results = await getResults(id);
  const finding = results?.findings.find((item) => item.finding_id === findingId);
  if (!finding) notFound();
  const { criterion } = finding;

  return (
    <>
      <PageHeader
        title={`${criterion.code} · ${criterion.name}`}
        actions={
          <Link
            href={`/app/evaluaciones/${id}/resultados`}
            className="text-primary text-sm hover:underline"
          >
            {copy.backToResults}
          </Link>
        }
      />
      <Card className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <FindingStatusBadge status={finding.status} />
          <p className="text-sm">{findingStatusDescriptions[finding.status]}</p>
        </div>
        <dl className="grid gap-3 text-sm sm:grid-cols-3">
          <div>
            <dt className="text-muted-foreground">{reviewCopy.priority}</dt>
            <dd>{priorityLabels[finding.priority]}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{reviewCopy.risk}</dt>
            <dd>{riskLabels[finding.risk_level]}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{reviewCopy.effort}</dt>
            <dd>{effortLabels[finding.effort]}</dd>
          </div>
        </dl>
        <div>
          <CardTitle>{reviewCopy.gap}</CardTitle>
          <p className="text-sm whitespace-pre-line">{finding.gap}</p>
        </div>
        <div>
          <CardTitle>{reviewCopy.recommendation}</CardTitle>
          <p className="text-sm whitespace-pre-line">{finding.recommendation}</p>
        </div>
        {finding.reviewer_comment ? (
          <div>
            <CardTitle>{copy.reviewerNotes}</CardTitle>
            <p className="text-sm whitespace-pre-line">{finding.reviewer_comment}</p>
          </div>
        ) : null}
      </Card>
      <Card className="flex flex-col gap-3">
        <CardTitle>{reviewCopy.evidenceTitle}</CardTitle>
        <EvidenceList
          evidence={finding.evidence.map((item) => ({ ...item, citation_verified: true }))}
        />
      </Card>
      <Card className="flex flex-col gap-3 text-sm">
        <CardTitle>{reviewCopy.criterionQuestion}</CardTitle>
        <p>{criterion.evaluation_question}</p>
        <CardTitle>{reviewCopy.expectedEvidence}</CardTitle>
        <p>{criterion.expected_evidence}</p>
        <CardTitle>{reviewCopy.references}</CardTitle>
        <ReferenceList
          item={{
            iso_reference: criterion.iso_reference,
            cis_reference: criterion.cis_reference,
            nist_reference: criterion.nist_reference,
            reference_status: criterion.reference_status === "confirmed" ? "confirmed" : "draft",
          }}
        />
      </Card>
      <Alert tone="neutral">{legal.scopeDisclaimer}</Alert>
    </>
  );
}
