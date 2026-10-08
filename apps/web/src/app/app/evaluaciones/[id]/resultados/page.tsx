import type { Metadata } from "next";
import Link from "next/link";

import { PageHeader } from "@/components/shared/PageHeader";
import { Alert } from "@/components/ui/alert";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { legal, resultsCopy as copy, surveyCopy } from "@/content/es";
import { getSurveyStatus } from "@/features/feedback";
import {
  CoverageCard,
  getResults,
  ImprovementPlan,
  ReportDownload,
  ResultsTable,
} from "@/features/results";
import { formatDate } from "@/lib/format";
import { requireRole } from "@/lib/guards";

export const metadata: Metadata = { title: copy.title };

export default async function ResultsPage({
  params,
}: PageProps<"/app/evaluaciones/[id]/resultados">) {
  const user = await requireRole("SME", "REVIEWER", "ADMIN");
  const { id } = await params;
  const results = await getResults(id);
  const survey = user.role === "SME" && results ? await getSurveyStatus(id) : null;

  if (!results) {
    return (
      <>
        <PageHeader title={copy.title} />
        <Alert tone="info">{copy.notAvailable}</Alert>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title={`${copy.title} · ${results.title}`}
        description={copy.approvedOn(formatDate(results.approved_at))}
        actions={
          <Link href={`/app/evaluaciones/${id}`} className="text-primary text-sm hover:underline">
            {results.title}
          </Link>
        }
      />
      <Alert tone="neutral">{legal.scopeDisclaimer}</Alert>
      {results.documents_retained_until ? (
        <p className="text-muted-foreground text-sm">
          {copy.retention(formatDate(results.documents_retained_until))}
        </p>
      ) : null}
      <CoverageCard coverage={results.coverage} />
      <ReportDownload evaluationId={id} canGenerate={user.role !== "SME"} />
      {survey ? (
        <Card className="flex flex-col gap-3">
          <CardTitle>{surveyCopy.title}</CardTitle>
          {survey.submitted_at ? (
            <CardDescription>{surveyCopy.thanks}</CardDescription>
          ) : (
            <>
              <CardDescription>{surveyCopy.invite}</CardDescription>
              <div>
                <Link
                  href={`/app/evaluaciones/${id}/encuesta`}
                  className={buttonVariants({ variant: "outline" })}
                >
                  {surveyCopy.open}
                </Link>
              </div>
            </>
          )}
        </Card>
      ) : null}
      <ImprovementPlan evaluationId={id} results={results} />
      <section aria-labelledby="hallazgos" className="flex flex-col gap-3">
        <h2 id="hallazgos" className="text-foreground text-lg font-semibold">
          {copy.findingsTitle}
        </h2>
        <ResultsTable evaluationId={id} findings={results.findings} />
      </section>
    </>
  );
}
