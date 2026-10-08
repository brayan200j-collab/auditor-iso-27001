import type { Metadata } from "next";
import Link from "next/link";

import { PageHeader } from "@/components/shared/PageHeader";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { checklistCopy, common, priorityLabels, table } from "@/content/es";
import { getChecklistVersion, PublishButton, ReferenceList } from "@/features/admin-checklist";
import { requireRole } from "@/lib/guards";

export const metadata: Metadata = { title: checklistCopy.title };

export default async function ChecklistVersionPage({
  params,
}: PageProps<"/app/admin/checklist/[id]">) {
  await requireRole("ADMIN");
  const { id } = await params;
  const version = await getChecklistVersion(id);
  const isDraft = version.status === "DRAFT";

  return (
    <>
      <PageHeader
        title={checklistCopy.version(version.version)}
        description={checklistCopy.items(version.active_item_count, version.item_count)}
        actions={
          <Link href="/app/admin/checklist" className="text-primary text-sm hover:underline">
            {common.back}
          </Link>
        }
      />
      {isDraft ? (
        <PublishButton versionId={version.id} />
      ) : (
        <Alert tone="neutral">{checklistCopy.readOnly}</Alert>
      )}
      <Table>
        <THead>
          <TR>
            <TH>{checklistCopy.columns.criterion}</TH>
            <TH>{checklistCopy.columns.priority}</TH>
            <TH>{checklistCopy.columns.references}</TH>
            <TH>{checklistCopy.columns.active}</TH>
            {isDraft ? (
              <TH>
                <span className="sr-only">{table.actions}</span>
              </TH>
            ) : null}
          </TR>
        </THead>
        <TBody>
          {version.items.map((item) => (
            <TR key={item.id}>
              <TD>
                <p className="font-medium">
                  {item.code} · {item.name}
                </p>
                <p className="text-muted-foreground mt-1 text-xs">{item.evaluation_question}</p>
              </TD>
              <TD>
                <Badge>{priorityLabels[item.priority]}</Badge>
              </TD>
              <TD>
                <ReferenceList item={item} />
              </TD>
              <TD>{item.active ? checklistCopy.yes : checklistCopy.no}</TD>
              {isDraft ? (
                <TD>
                  <Link
                    href={`/app/admin/checklist/${version.id}/${item.code}`}
                    className="text-primary underline-offset-4 hover:underline"
                  >
                    {checklistCopy.edit}
                    <span className="sr-only"> {item.code}</span>
                  </Link>
                </TD>
              ) : null}
            </TR>
          ))}
        </TBody>
      </Table>
    </>
  );
}
