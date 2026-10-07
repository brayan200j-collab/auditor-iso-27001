import type { Metadata } from "next";

import { EvaluationStatusBadge } from "@/components/shared/EvaluationStatusBadge";
import { PageHeader } from "@/components/shared/PageHeader";
import { ProgressTimeline } from "@/components/shared/ProgressTimeline";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { consentCopy, evaluations } from "@/content/es";
import {
  ConsentForm,
  EvaluationNotices,
  getConsentText,
  getEvaluation,
} from "@/features/evaluations";
import { requireRole } from "@/lib/guards";

export const metadata: Metadata = { title: evaluations.listTitle };

const OPEN_FOR_DOCUMENTS = new Set(["DRAFT", "RECEIVED", "REJECTED"]);

export default async function EvaluationPage({ params }: PageProps<"/app/evaluaciones/[id]">) {
  await requireRole("SME");
  const { id } = await params;
  const detail = await getEvaluation(id);
  const { evaluation } = detail;
  const needsConsent = !detail.consent_given && OPEN_FOR_DOCUMENTS.has(evaluation.status);
  const consent = needsConsent ? await getConsentText() : null;

  return (
    <>
      <PageHeader
        title={evaluation.title}
        actions={<EvaluationStatusBadge status={evaluation.status} />}
      />
      <EvaluationNotices evaluation={evaluation} />
      <Card className="flex flex-col gap-4">
        <CardTitle>{evaluations.progressTitle}</CardTitle>
        <ProgressTimeline steps={detail.progress} />
      </Card>
      {consent ? (
        <Card className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <CardTitle>{consentCopy.title}</CardTitle>
            <CardDescription>{consentCopy.description}</CardDescription>
          </div>
          <ConsentForm evaluationId={evaluation.id} version={consent.version} text={consent.text} />
        </Card>
      ) : null}
    </>
  );
}
