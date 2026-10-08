import { EmptyState } from "@/components/shared/EmptyState";
import { Badge } from "@/components/ui/badge";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { auditCopy as copy, roleLabels } from "@/content/es";
import { formatDateTime } from "@/lib/format";

import type { AuditLogPage } from "./data";

const TONES = { SUCCESS: "success", DENIED: "warning", FAILURE: "danger" } as const;

export function AuditLogTable({ items }: { items: AuditLogPage["items"] }) {
  if (items.length === 0) return <EmptyState message={copy.empty} />;
  return (
    <Table>
      <THead>
        <TR>
          <TH>{copy.columns.when}</TH>
          <TH>{copy.columns.action}</TH>
          <TH>{copy.columns.outcome}</TH>
          <TH>{copy.columns.role}</TH>
          <TH>{copy.columns.resource}</TH>
        </TR>
      </THead>
      <TBody>
        {items.map((entry) => (
          <TR key={entry.id}>
            <TD className="whitespace-nowrap">{formatDateTime(entry.occurred_at)}</TD>
            <TD>{copy.actions[entry.action] ?? "—"}</TD>
            <TD>
              <Badge tone={TONES[entry.outcome]}>{copy.outcomes[entry.outcome]}</Badge>
            </TD>
            <TD>
              {entry.actor_role
                ? (roleLabels[entry.actor_role as keyof typeof roleLabels] ?? "—")
                : "—"}
            </TD>
            <TD>
              {entry.resource_type ? (copy.resources[entry.resource_type] ?? "—") : "—"}
              {entry.resource_id ? (
                <span className="text-muted-foreground block font-mono text-xs">
                  {entry.resource_id.slice(0, 8)}
                </span>
              ) : null}
            </TD>
          </TR>
        ))}
      </TBody>
    </Table>
  );
}
