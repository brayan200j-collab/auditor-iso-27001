import Link from "next/link";

import { EmptyState } from "@/components/shared/EmptyState";
import { Badge } from "@/components/ui/badge";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { adminUsers, roleLabels, table } from "@/content/es";
import { formatDate } from "@/lib/format";

import type { User } from "./data";

type UsersTableProps = { users: User[]; companyNames: Record<string, string> };

export function UsersTable({ users, companyNames }: UsersTableProps) {
  if (users.length === 0) return <EmptyState message={adminUsers.empty} />;
  return (
    <Table>
      <THead>
        <TR>
          <TH>{adminUsers.fullName}</TH>
          <TH>{adminUsers.email}</TH>
          <TH>{adminUsers.role}</TH>
          <TH>{adminUsers.company}</TH>
          <TH>{adminUsers.status}</TH>
          <TH>{table.createdAt}</TH>
          <TH>
            <span className="sr-only">{table.actions}</span>
          </TH>
        </TR>
      </THead>
      <TBody>
        {users.map((user) => (
          <TR key={user.id}>
            <TD className="font-medium">{user.full_name}</TD>
            <TD>{user.email}</TD>
            <TD>{roleLabels[user.role]}</TD>
            <TD>{user.company_id ? (companyNames[user.company_id] ?? "—") : "—"}</TD>
            <TD>
              <Badge tone={user.active ? "success" : "neutral"}>
                {user.active ? adminUsers.activeLabel : adminUsers.inactiveLabel}
              </Badge>
            </TD>
            <TD>{formatDate(user.created_at)}</TD>
            <TD>
              <Link
                href={`/app/admin/usuarios/${user.id}`}
                className="text-primary underline-offset-4 hover:underline"
              >
                {adminUsers.edit}
                <span className="sr-only"> {user.full_name}</span>
              </Link>
            </TD>
          </TR>
        ))}
      </TBody>
    </Table>
  );
}
