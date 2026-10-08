import type { Metadata } from "next";
import Link from "next/link";

import { PageHeader } from "@/components/shared/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { adminUsers, common, roleLabels } from "@/content/es";
import { companyOptions } from "@/features/admin-companies";
import { EditUserForm, getUser } from "@/features/admin-users";
import { requireRole } from "@/lib/guards";

export const metadata: Metadata = { title: adminUsers.editTitle };

export default async function EditUserPage({ params }: PageProps<"/app/admin/usuarios/[id]">) {
  await requireRole("ADMIN");
  const { id } = await params;
  const [user, companies] = await Promise.all([getUser(id), companyOptions()]);

  return (
    <>
      <PageHeader
        title={adminUsers.editTitle}
        description={`${user.email} · ${roleLabels[user.role]}`}
        actions={
          <Link href="/app/admin/usuarios" className="text-primary text-sm hover:underline">
            {common.back}
          </Link>
        }
      />
      <Badge tone={user.active ? "success" : "neutral"} className="self-start">
        {user.active ? adminUsers.activeLabel : adminUsers.inactiveLabel}
      </Badge>
      <Card>
        <EditUserForm
          userId={user.id}
          isSme={user.role === "SME"}
          active={user.active}
          defaults={{ fullName: user.full_name, companyId: user.company_id ?? "" }}
          companies={companies.map(({ id: companyId, name }) => ({ id: companyId, name }))}
        />
      </Card>
    </>
  );
}
