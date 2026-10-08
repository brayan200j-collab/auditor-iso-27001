import type { Metadata } from "next";

import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/ui/card";
import { evaluations } from "@/content/es";
import { CreateEvaluationForm } from "@/features/evaluations";
import { requireRole } from "@/lib/guards";

export const metadata: Metadata = { title: evaluations.newTitle };

export default async function NewEvaluationPage() {
  await requireRole("SME");
  return (
    <>
      <PageHeader title={evaluations.newTitle} />
      <Card className="max-w-2xl">
        <CreateEvaluationForm />
      </Card>
    </>
  );
}
