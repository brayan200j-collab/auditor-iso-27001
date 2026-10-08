import type { Metadata } from "next";
import Link from "next/link";

import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/ui/card";
import { adminCompanies, common } from "@/content/es";
import { CompanyForm, getCompany } from "@/features/admin-companies";
import { requireRole } from "@/lib/guards";

export const metadata: Metadata = { title: adminCompanies.editTitle };

export default async function EditCompanyPage({ params }: PageProps<"/app/admin/empresas/[id]">) {
  await requireRole("ADMIN");
  const { id } = await params;
  const company = await getCompany(id);

  return (
    <>
      <PageHeader
        title={adminCompanies.editTitle}
        description={company.name}
        actions={
          <Link href="/app/admin/empresas" className="text-primary text-sm hover:underline">
            {common.back}
          </Link>
        }
      />
      <Card>
        <CompanyForm
          companyId={company.id}
          defaults={{
            name: company.name,
            taxId: company.tax_id ?? "",
            sector: company.sector ?? "",
            city: company.city ?? "",
            active: company.active,
          }}
        />
      </Card>
    </>
  );
}
