import type { Metadata } from "next";

import { EvaluationStatusBadge } from "@/components/shared/EvaluationStatusBadge";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardTitle } from "@/components/ui/card";
import { evaluations } from "@/content/es";
import { EvaluationNotices, getEvaluation } from "@/features/evaluations";
import { ProcessingAction, StatusTracker } from "@/features/processing";
import { requireRole } from "@/lib/guards";

export const metadata: Metadata = { title: evaluations.reviewerTitle };

export default async function ReviewEvaluationPage({ params }: PageProps<"/app/revision/[id]">) {
  await requireRole("REVIEWER", "ADMIN");
  const { id } = await params;
  const detail = await getEvaluation(id);
  const { evaluation } = detail;

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
    </>
  );
}
