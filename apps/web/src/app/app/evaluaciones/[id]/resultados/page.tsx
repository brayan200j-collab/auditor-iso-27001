import type { Metadata } from "next";
import Link from "next/link";

import { PageHeader } from "@/components/shared/PageHeader";
import { Alert } from "@/components/ui/alert";
import { legal, resultsCopy as copy } from "@/content/es";
import { CoverageCard, getResults, ImprovementPlan, ResultsTable } from "@/features/results";
import { formatDate } from "@/lib/format";
import { requireRole } from "@/lib/guards";

export const metadata: Metadata = { title: copy.title };

export default async function ResultsPage({
  params,
}: PageProps<"/app/evaluaciones/[id]/resultados">) {
  await requireRole("SME", "REVIEWER", "ADMIN");
  const { id } = await params;
  const results = await getResults(id);

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
      <CoverageCard coverage={results.coverage} />
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
