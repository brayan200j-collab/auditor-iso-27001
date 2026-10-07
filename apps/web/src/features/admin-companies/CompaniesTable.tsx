import Link from "next/link";

import { EmptyState } from "@/components/shared/EmptyState";
import { Badge } from "@/components/ui/badge";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { adminCompanies, table } from "@/content/es";
import { formatDate } from "@/lib/format";

import type { Company } from "./data";

export function CompaniesTable({ companies }: { companies: Company[] }) {
  if (companies.length === 0) return <EmptyState message={adminCompanies.empty} />;
  return (
    <Table>
      <THead>
        <TR>
          <TH>{adminCompanies.name}</TH>
          <TH>{adminCompanies.taxId}</TH>
          <TH>{adminCompanies.city}</TH>
          <TH>{adminCompanies.status}</TH>
          <TH>{table.createdAt}</TH>
          <TH>
            <span className="sr-only">{table.actions}</span>
          </TH>
        </TR>
      </THead>
      <TBody>
        {companies.map((company) => (
          <TR key={company.id}>
            <TD className="font-medium">{company.name}</TD>
            <TD>{company.tax_id ?? "—"}</TD>
            <TD>{company.city ?? "—"}</TD>
            <TD>
              <Badge tone={company.active ? "success" : "neutral"}>
                {company.active ? adminCompanies.activeLabel : adminCompanies.inactiveLabel}
              </Badge>
            </TD>
            <TD>{formatDate(company.created_at)}</TD>
            <TD>
              <Link
                href={`/app/admin/empresas/${company.id}`}
                className="text-primary underline-offset-4 hover:underline"
              >
                {adminCompanies.edit}
                <span className="sr-only"> {company.name}</span>
              </Link>
            </TD>
          </TR>
        ))}
      </TBody>
    </Table>
  );
}
