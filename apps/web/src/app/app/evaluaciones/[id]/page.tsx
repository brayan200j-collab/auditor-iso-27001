import type { Metadata } from "next";
import Link from "next/link";

import { EvaluationStatusBadge } from "@/components/shared/EvaluationStatusBadge";
import { PageHeader } from "@/components/shared/PageHeader";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { consentCopy, documentsCopy, evaluations, resultsCopy } from "@/content/es";
import { DocumentList, listDocuments, UploadZone } from "@/features/documents";
import {
  ConsentForm,
  EvaluationNotices,
  getConsentText,
  getEvaluation,
} from "@/features/evaluations";
import { ProcessingAction, StatusTracker } from "@/features/processing";
import { requireRole } from "@/lib/guards";

export const metadata: Metadata = { title: evaluations.listTitle };

const OPEN_FOR_DOCUMENTS = new Set(["DRAFT", "RECEIVED", "REJECTED"]);
const DELETABLE = new Set(["DRAFT", "RECEIVED"]);

export default async function EvaluationPage({ params }: PageProps<"/app/evaluaciones/[id]">) {
  await requireRole("SME");
  const { id } = await params;
  const detail = await getEvaluation(id);
  const { evaluation } = detail;
  const needsConsent = !detail.consent_given && OPEN_FOR_DOCUMENTS.has(evaluation.status);
  const [consent, documents] = await Promise.all([
    needsConsent ? getConsentText() : Promise.resolve(null),
    listDocuments(evaluation.id),
  ]);
  const canUpload = detail.consent_given && OPEN_FOR_DOCUMENTS.has(evaluation.status);

  return (
    <>
      <PageHeader
        title={evaluation.title}
        actions={<EvaluationStatusBadge status={evaluation.status} />}
      />
      <EvaluationNotices evaluation={evaluation} />
      {evaluation.status === "APPROVED" ? (
        <Card className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <CardTitle>{resultsCopy.readyTitle}</CardTitle>
            <CardDescription>{resultsCopy.readyDescription}</CardDescription>
          </div>
          <div>
            <Link
              href={`/app/evaluaciones/${evaluation.id}/resultados`}
              className={buttonVariants()}
            >
              {resultsCopy.open}
            </Link>
          </div>
        </Card>
      ) : null}
      <Card className="flex flex-col gap-4">
        <CardTitle>{evaluations.progressTitle}</CardTitle>
        <StatusTracker
          evaluationId={evaluation.id}
          initialStatus={evaluation.status}
          initialSteps={detail.progress}
        />
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
      <Card className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <CardTitle>{documentsCopy.title}</CardTitle>
          <CardDescription>{documentsCopy.description}</CardDescription>
        </div>
        {canUpload ? <UploadZone evaluationId={evaluation.id} /> : null}
        <DocumentList
          evaluationId={evaluation.id}
          documents={documents}
          canDelete={DELETABLE.has(evaluation.status)}
        />
        {detail.available_actions.includes("START_ANALYSIS") && documents.length > 0 ? (
          <ProcessingAction evaluationId={evaluation.id} kind="start" />
        ) : null}
      </Card>
    </>
  );
}
