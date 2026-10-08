"use server";

import { revalidatePath } from "next/cache";

import { adminCompanies } from "@/content/es";
import { failure, type ActionResult } from "@/lib/actions";
import { serverApi } from "@/lib/api/server";

import { companySchema } from "./schemas";

function payload(input: unknown) {
  const parsed = companySchema.safeParse(input);
  if (!parsed.success) return null;
  const { name, taxId, sector, city, active } = parsed.data;
  return {
    body: { name, tax_id: taxId || null, sector: sector || null, city: city || null },
    active,
  };
}

export async function createCompanyAction(input: unknown): Promise<ActionResult> {
  const values = payload(input);
  if (!values) return { ok: false, message: adminCompanies.validation.name };
  const api = await serverApi();
  const { error } = await api.POST("/api/v1/companies", { body: values.body });
  if (error) return failure(error);
  revalidatePath("/app/admin/empresas");
  return { ok: true, message: adminCompanies.created };
}

export async function updateCompanyAction(
  companyId: string,
  input: unknown,
): Promise<ActionResult> {
  const values = payload(input);
  if (!values) return { ok: false, message: adminCompanies.validation.name };
  const api = await serverApi();
  const { error } = await api.PATCH("/api/v1/companies/{company_id}", {
    params: { path: { company_id: companyId } },
    body: { ...values.body, active: values.active },
  });
  if (error) return failure(error);
  revalidatePath("/app/admin/empresas");
  return { ok: true, message: adminCompanies.updated };
}
