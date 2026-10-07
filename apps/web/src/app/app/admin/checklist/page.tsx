import type { Metadata } from "next";
import Link from "next/link";

import { PageHeader } from "@/components/shared/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Card, CardTitle } from "@/components/ui/card";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { checklistCopy, table } from "@/content/es";
import { CreateDraftButton, listChecklistVersions } from "@/features/admin-checklist";
import { formatDate } from "@/lib/format";
import { requireRole } from "@/lib/guards";

export const metadata: Metadata = { title: checklistCopy.title };

export default async function ChecklistVersionsPage() {
  await requireRole("ADMIN");
  const versions = await listChecklistVersions();
  const hasDraft = versions.some((version) => version.status === "DRAFT");

  return (
    <>
      <PageHeader title={checklistCopy.title} description={checklistCopy.description} />
      <Card className="flex flex-col gap-4">
        <CardTitle>{checklistCopy.versionsTitle}</CardTitle>
        {hasDraft ? null : <CreateDraftButton />}
        <Table>
          <THead>
            <TR>
              <TH>{checklistCopy.title}</TH>
              <TH>{checklistCopy.columns.active}</TH>
              <TH>{checklistCopy.publishedAt}</TH>
              <TH>
                <span className="sr-only">{table.actions}</span>
              </TH>
            </TR>
          </THead>
          <TBody>
            {versions.map((version) => (
              <TR key={version.id}>
                <TD className="font-medium">
                  {checklistCopy.version(version.version)}{" "}
                  <Badge tone={version.status === "PUBLISHED" ? "success" : "warning"}>
                    {checklistCopy.statuses[version.status]}
                  </Badge>
                </TD>
                <TD>{checklistCopy.items(version.active_item_count, version.item_count)}</TD>
                <TD>{formatDate(version.published_at)}</TD>
                <TD>
                  <Link
                    href={`/app/admin/checklist/${version.id}`}
                    className="text-primary underline-offset-4 hover:underline"
                  >
                    {checklistCopy.view}
                    <span className="sr-only"> {checklistCopy.version(version.version)}</span>
                  </Link>
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </Card>
    </>
  );
}
