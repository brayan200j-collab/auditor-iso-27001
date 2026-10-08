import type { Metadata } from "next";

import { PageHeader } from "@/components/shared/PageHeader";
import { Pagination } from "@/components/shared/Pagination";
import { SearchForm } from "@/components/shared/SearchForm";
import { Card, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/input";
import { adminUsers, filterLabels, roleLabels } from "@/content/es";
import { companyOptions } from "@/features/admin-companies";
import {
  CreateUserForm,
  listUsers,
  ROLES,
  UsersTable,
  type UserRole,
} from "@/features/admin-users";
import { pageParam, textParam } from "@/lib/format";
import { requireRole } from "@/lib/guards";

export const metadata: Metadata = { title: adminUsers.title };

function roleParam(value: string | string[] | undefined): UserRole | undefined {
  const role = Array.isArray(value) ? value[0] : value;
  return ROLES.find((candidate) => candidate === role);
}

export default async function UsersPage({ searchParams }: PageProps<"/app/admin/usuarios">) {
  await requireRole("ADMIN");
  const params = await searchParams;
  const page = pageParam(params.page);
  const search = textParam(params.search);
  const role = roleParam(params.role);
  const [result, companies] = await Promise.all([
    listUsers({ page, role, search }),
    companyOptions(),
  ]);
  const companyNames = Object.fromEntries(companies.map((company) => [company.id, company.name]));

  return (
    <>
      <PageHeader title={adminUsers.title} description={adminUsers.description} />
      <Card className="flex flex-col gap-4">
        <CardTitle>{adminUsers.newTitle}</CardTitle>
        <CreateUserForm companies={companies.map(({ id, name }) => ({ id, name }))} />
      </Card>
      <SearchForm
        label={adminUsers.searchLabel}
        submitLabel={adminUsers.search}
        defaultValue={search}
      >
        <div className="flex flex-col gap-1.5">
          <label htmlFor="role-filter" className="text-foreground text-sm font-medium">
            {adminUsers.filterRole}
          </label>
          <Select id="role-filter" name="role" defaultValue={role ?? ""}>
            <option value="">{filterLabels.ALL}</option>
            {ROLES.map((value) => (
              <option key={value} value={value}>
                {roleLabels[value]}
              </option>
            ))}
          </Select>
        </div>
      </SearchForm>
      <UsersTable users={result.items} companyNames={companyNames} />
      <Pagination
        page={result.meta.page}
        pageSize={result.meta.page_size}
        total={result.meta.total}
        hrefFor={(target) =>
          `/app/admin/usuarios?${new URLSearchParams({
            page: String(target),
            ...(search ? { search } : {}),
            ...(role ? { role } : {}),
          })}`
        }
      />
    </>
  );
}
