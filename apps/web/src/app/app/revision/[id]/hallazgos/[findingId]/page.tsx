import type { Metadata } from "next";
import Link from "next/link";

import { FindingStatusBadge, ReviewStatusBadge } from "@/components/shared/FindingStatusBadge";
import { PageHeader } from "@/components/shared/PageHeader";
import { Alert } from "@/components/ui/alert";
import { Card, CardTitle } from "@/components/ui/card";
import { effortLabels, priorityLabels, reviewCopy, riskLabels } from "@/content/es";
import { ReferenceList } from "@/features/admin-checklist";
import { ConfidenceValue, EvidenceList, FindingActions, getFinding } from "@/features/review";
import { formatDateTime } from "@/lib/format";
import { requireRole } from "@/lib/guards";

export const metadata: Metadata = { title: reviewCopy.queueTitle };

export default async function FindingReviewPage({
  params,
}: PageProps<"/app/revision/[id]/hallazgos/[findingId]">) {
  await requireRole("REVIEWER", "ADMIN");
  const { findingId } = await params;
  const detail = await getFinding(findingId);
  const { item } = detail;
  const { ai, criterion } = item;
  const current = item.review.final;
  const editable = detail.evaluation_status === "PENDING_REVIEW";

  return (
    <>
      <PageHeader
        title={`${criterion.code} · ${criterion.name}`}
        actions={
          <Link
            href={`/app/revision/${detail.evaluation_id}`}
            className="text-primary text-sm hover:underline"
          >
            {reviewCopy.backToQueue}
          </Link>
        }
      />
      <div className="flex flex-wrap items-center gap-2">
        <FindingStatusBadge status={ai.status} />
        <ReviewStatusBadge status={item.review.review_status} />
      </div>
      {ai.status === null ? <Alert tone="danger">{reviewCopy.modelError}</Alert> : null}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="flex flex-col gap-4 lg:col-span-2">
          <CardTitle>{reviewCopy.aiStatus}</CardTitle>
          <dl className="grid gap-3 text-sm sm:grid-cols-3">
            <div>
              <dt className="text-muted-foreground">{reviewCopy.priority}</dt>
              <dd>{ai.preliminary_priority ? priorityLabels[ai.preliminary_priority] : "—"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">{reviewCopy.risk}</dt>
              <dd>{ai.risk_level ? riskLabels[ai.risk_level] : "—"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">{reviewCopy.effort}</dt>
              <dd>{ai.estimated_effort ? effortLabels[ai.estimated_effort] : "—"}</dd>
            </div>
          </dl>
          <div>
            <h3 className="text-foreground text-sm font-semibold">{reviewCopy.gap}</h3>
            <p className="text-foreground text-sm whitespace-pre-line">{ai.gap || "—"}</p>
          </div>
          <div>
            <h3 className="text-foreground text-sm font-semibold">{reviewCopy.recommendation}</h3>
            <p className="text-foreground text-sm whitespace-pre-line">
              {ai.recommendation || "—"}
            </p>
          </div>
          <div>
            <h3 className="text-foreground mb-2 text-sm font-semibold">
              {reviewCopy.evidenceTitle}
            </h3>
            <EvidenceList evidence={ai.evidence} evaluationId={detail.evaluation_id} />
          </div>
          <p className="text-muted-foreground text-xs">
            {reviewCopy.modelInfo(
              ai.provider,
              ai.model,
              ai.prompt_version,
              formatDateTime(ai.created_at),
            )}
          </p>
        </Card>
        <div className="flex flex-col gap-6">
          <Card className="flex flex-col gap-3">
            <ConfidenceValue value={ai.confidence} />
          </Card>
          <Card className="flex flex-col gap-3 text-sm">
            <h3 className="text-foreground font-semibold">{reviewCopy.criterionQuestion}</h3>
            <p>{criterion.evaluation_question}</p>
            <h3 className="text-foreground font-semibold">{reviewCopy.expectedEvidence}</h3>
            <p>{criterion.expected_evidence}</p>
            <h3 className="text-foreground font-semibold">{reviewCopy.references}</h3>
            <ReferenceList
              item={{
                iso_reference: criterion.iso_reference,
                cis_reference: criterion.cis_reference,
                nist_reference: criterion.nist_reference,
                reference_status:
                  criterion.reference_status === "confirmed" ? "confirmed" : "draft",
              }}
            />
          </Card>
        </div>
      </div>

      <Card className="flex flex-col gap-4">
        <CardTitle>{reviewCopy.actions.choose}</CardTitle>
        {editable ? (
          <FindingActions
            evaluationId={detail.evaluation_id}
            findingId={item.finding_id}
            canApprove={ai.status !== null}
            defaults={{
              status: current?.status ?? ai.status ?? "PARTIAL",
              gap: current?.gap ?? ai.gap,
              recommendation: current?.recommendation ?? ai.recommendation,
              priority: current?.priority ?? ai.preliminary_priority ?? "MEDIUM",
              risk_level: current?.risk_level ?? ai.risk_level ?? "MEDIUM",
              effort: current?.effort ?? ai.estimated_effort ?? "MEDIUM",
              comment: "",
            }}
          />
        ) : (
          <Alert tone="neutral">{reviewCopy.locked}</Alert>
        )}
      </Card>

      {detail.history.length > 0 ? (
        <Card className="flex flex-col gap-2">
          <CardTitle>{reviewCopy.history}</CardTitle>
          <ul className="text-sm">
            {detail.history.map((entry) => (
              <li key={entry.created_at} className="border-border border-b py-2 last:border-0">
                <span className="font-medium">{reviewCopy.historyActions[entry.action]}</span> ·{" "}
                {formatDateTime(entry.created_at)}
                {entry.comment ? <p className="text-muted-foreground">{entry.comment}</p> : null}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}
    </>
  );
}
