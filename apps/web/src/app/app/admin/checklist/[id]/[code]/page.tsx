import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/ui/card";
import { checklistCopy, common } from "@/content/es";
import { getChecklistVersion, ItemForm } from "@/features/admin-checklist";
import { requireRole } from "@/lib/guards";

export const metadata: Metadata = { title: checklistCopy.title };

export default async function ChecklistItemPage({
  params,
}: PageProps<"/app/admin/checklist/[id]/[code]">) {
  await requireRole("ADMIN");
  const { id, code } = await params;
  const version = await getChecklistVersion(id);
  const item = version.items.find((candidate) => candidate.code === code);
  if (!item || version.status !== "DRAFT") notFound();

  return (
    <>
      <PageHeader
        title={checklistCopy.editTitle(item.code)}
        description={`${checklistCopy.version(version.version)} · ${item.name}`}
        actions={
          <Link
            href={`/app/admin/checklist/${version.id}`}
            className="text-primary text-sm hover:underline"
          >
            {common.back}
          </Link>
        }
      />
      <Card>
        <ItemForm
          versionId={version.id}
          code={item.code}
          defaults={{
            name: item.name,
            description: item.description,
            evaluation_question: item.evaluation_question,
            expected_evidence: item.expected_evidence,
            iso_reference: item.iso_reference ?? "",
            cis_reference: item.cis_reference ?? "",
            nist_reference: item.nist_reference ?? "",
            reference_status: item.reference_status,
            keywords: item.keywords.join(", "),
            priority: item.priority,
            risk_level: item.risk_level,
            effort: item.effort,
            active: item.active,
          }}
        />
      </Card>
    </>
  );
}
