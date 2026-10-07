import type { Metadata } from "next";

import { PageHeader } from "@/components/shared/PageHeader";
import { Pagination } from "@/components/shared/Pagination";
import { SearchForm } from "@/components/shared/SearchForm";
import { Card, CardTitle } from "@/components/ui/card";
import { adminCompanies } from "@/content/es";
import { CompaniesTable, CompanyForm, listCompanies } from "@/features/admin-companies";
import { pageParam, textParam } from "@/lib/format";
import { requireRole } from "@/lib/guards";

export const metadata: Metadata = { title: adminCompanies.title };

export default async function CompaniesPage({ searchParams }: PageProps<"/app/admin/empresas">) {
  await requireRole("ADMIN");
  const params = await searchParams;
  const page = pageParam(params.page);
  const search = textParam(params.search);
  const result = await listCompanies(page, search);

  return (
    <>
      <PageHeader title={adminCompanies.title} description={adminCompanies.description} />
      <Card className="flex flex-col gap-4">
        <CardTitle>{adminCompanies.newTitle}</CardTitle>
        <CompanyForm />
      </Card>
      <SearchForm
        label={adminCompanies.searchLabel}
        submitLabel={adminCompanies.search}
        defaultValue={search}
      />
      <CompaniesTable companies={result.items} />
      <Pagination
        page={result.meta.page}
        pageSize={result.meta.page_size}
        total={result.meta.total}
        hrefFor={(target) =>
          `/app/admin/empresas?${new URLSearchParams({ page: String(target), ...(search ? { search } : {}) })}`
        }
      />
    </>
  );
}
