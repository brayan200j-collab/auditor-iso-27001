import type { Metadata } from "next";
import Link from "next/link";

import { EvaluationStatusBadge } from "@/components/shared/EvaluationStatusBadge";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { evaluations, resultsCopy, reviewCopy } from "@/content/es";
import { listDocuments } from "@/features/documents";
import { EvaluationNotices, getEvaluation } from "@/features/evaluations";
import { ProcessingAction, StatusTracker } from "@/features/processing";
import {
  DecisionPanel,
  getReview,
  ReviewDocuments,
  ReviewQueueTable,
  ReviewSummaryCard,
} from "@/features/review";
import { requireRole } from "@/lib/guards";

export const metadata: Metadata = { title: evaluations.reviewerTitle };

const WITH_FINDINGS = new Set(["PENDING_REVIEW", "APPROVED", "REJECTED"]);

export default async function ReviewEvaluationPage({ params }: PageProps<"/app/revision/[id]">) {
  await requireRole("REVIEWER", "ADMIN");
  const { id } = await params;
  const detail = await getEvaluation(id);
  const { evaluation } = detail;
  const [review, documents] = await Promise.all([
    WITH_FINDINGS.has(evaluation.status) ? getReview(evaluation.id) : Promise.resolve(null),
    listDocuments(evaluation.id),
  ]);

  return (
    <>
      <PageHeader
        title={evaluation.title}
        description={evaluation.company_name ?? undefined}
        actions={<EvaluationStatusBadge status={evaluation.status} />}
      />
      <EvaluationNotices evaluation={evaluation} />
      <Card className="flex flex-col gap-4">
        <CardTitle>{evaluations.progressTitle}</CardTitle>
        <StatusTracker
          evaluationId={evaluation.id}
          initialStatus={evaluation.status}
          initialSteps={detail.progress}
        />
      </Card>
      {evaluation.status === "FAILED" ? (
        <ProcessingAction evaluationId={evaluation.id} kind="retry" />
      ) : null}
      {documents.length > 0 ? (
        <ReviewDocuments evaluationId={evaluation.id} documents={documents} />
      ) : null}
      {review ? (
        <>
          <ReviewSummaryCard summary={review.summary} />
          <section aria-labelledby="cola" className="flex flex-col gap-3">
            <div className="flex flex-col gap-1">
              <h2 id="cola" className="text-foreground text-lg font-semibold">
                {reviewCopy.queueTitle}
              </h2>
              <CardDescription>{reviewCopy.queueHint}</CardDescription>
            </div>
            <ReviewQueueTable evaluationId={evaluation.id} items={review.items} />
          </section>
          {evaluation.status === "PENDING_REVIEW" ? (
            <DecisionPanel evaluationId={evaluation.id} pending={review.summary.pending} />
          ) : null}
          {evaluation.status === "APPROVED" ? (
            <Link
              href={`/app/evaluaciones/${evaluation.id}/resultados`}
              className="text-primary text-sm hover:underline"
            >
              {resultsCopy.open}
            </Link>
          ) : null}
        </>
      ) : null}
    </>
  );
}
