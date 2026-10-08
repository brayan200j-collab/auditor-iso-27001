import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { PageHeader } from "@/components/shared/PageHeader";
import { Alert } from "@/components/ui/alert";
import { Card } from "@/components/ui/card";
import { surveyCopy as copy } from "@/content/es";
import { getSurveyStatus, SurveyForm } from "@/features/feedback";
import { requireRole } from "@/lib/guards";

export const metadata: Metadata = { title: copy.title };

export default async function SurveyPage({ params }: PageProps<"/app/evaluaciones/[id]/encuesta">) {
  await requireRole("SME");
  const { id } = await params;
  const status = await getSurveyStatus(id);
  if (!status?.available) notFound();

  return (
    <>
      <PageHeader
        title={copy.title}
        description={copy.description}
        actions={
          <Link
            href={`/app/evaluaciones/${id}/resultados`}
            className="text-primary text-sm hover:underline"
          >
            {copy.back}
          </Link>
        }
      />
      <Card>
        {status.submitted_at ? (
          <Alert tone="success">{copy.thanks}</Alert>
        ) : (
          <SurveyForm evaluationId={id} />
        )}
      </Card>
    </>
  );
}
