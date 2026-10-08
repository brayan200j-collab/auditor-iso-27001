import type { Metadata } from "next";

import { PageHeader } from "@/components/shared/PageHeader";
import { Pagination } from "@/components/shared/Pagination";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/input";
import { auditCopy as copy } from "@/content/es";
import {
  AuditLogTable,
  listAuditLogs,
  type AuditAction,
  type AuditOutcome,
} from "@/features/metrics";
import { pageParam } from "@/lib/format";
import { requireRole } from "@/lib/guards";

export const metadata: Metadata = { title: copy.title };

function pick<T extends string>(value: unknown, allowed: readonly T[]): T | undefined {
  return typeof value === "string" && (allowed as readonly string[]).includes(value)
    ? (value as T)
    : undefined;
}

const ACTIONS = Object.keys(copy.actions) as AuditAction[];
const OUTCOMES = Object.keys(copy.outcomes) as AuditOutcome[];

export default async function AuditLogPage({ searchParams }: PageProps<"/app/admin/auditoria">) {
  await requireRole("ADMIN");
  const params = await searchParams;
  const page = pageParam(params.page);
  const action = pick(params.action, ACTIONS);
  const outcome = pick(params.outcome, OUTCOMES);
  const result = await listAuditLogs({ page, action, outcome });

  const query = (target: number) => {
    const search = new URLSearchParams({ page: String(target) });
    if (action) search.set("action", action);
    if (outcome) search.set("outcome", outcome);
    return `/app/admin/auditoria?${search.toString()}`;
  };

  return (
    <>
      <PageHeader title={copy.title} description={copy.description} />
      <form method="get" className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-1.5">
          <label htmlFor="audit-action" className="text-sm font-medium">
            {copy.filterAction}
          </label>
          <Select id="audit-action" name="action" defaultValue={action ?? ""} className="w-64">
            <option value="">{copy.all}</option>
            {ACTIONS.map((value) => (
              <option key={value} value={value}>
                {copy.actions[value]}
              </option>
            ))}
          </Select>
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="audit-outcome" className="text-sm font-medium">
            {copy.filterOutcome}
          </label>
          <Select id="audit-outcome" name="outcome" defaultValue={outcome ?? ""} className="w-48">
            <option value="">{copy.all}</option>
            {OUTCOMES.map((value) => (
              <option key={value} value={value}>
                {copy.outcomes[value]}
              </option>
            ))}
          </Select>
        </div>
        <Button type="submit" variant="outline">
          {copy.apply}
        </Button>
      </form>
      <AuditLogTable items={result?.items ?? []} />
      {result ? (
        <Pagination
          page={result.meta.page}
          pageSize={result.meta.page_size}
          total={result.meta.total}
          hrefFor={query}
        />
      ) : null}
    </>
  );
}
