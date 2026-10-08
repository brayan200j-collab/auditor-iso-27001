import "server-only";

import { notFound } from "next/navigation";

import type { components } from "@/lib/api/schema";
import { serverApi } from "@/lib/api/server";

export type Company = components["schemas"]["CompanyResponse"];
export type CompanyPage = components["schemas"]["CompanyPage"];

export async function listCompanies(page: number, search?: string): Promise<CompanyPage> {
  const api = await serverApi();
  const { data, error } = await api.GET("/api/v1/companies", {
    params: { query: { page, page_size: 20, ...(search ? { search } : {}) } },
  });
  if (!data) throw new Error(`Unable to list companies: ${JSON.stringify(error)}`);
  return data;
}

/** All active companies, for selectors (the pilot has only a handful). */
export async function companyOptions(): Promise<Company[]> {
  const page = await listCompanies(1);
  return page.items.filter((company) => company.active);
}

export async function getCompany(companyId: string): Promise<Company> {
  const api = await serverApi();
  const { data } = await api.GET("/api/v1/companies/{company_id}", {
    params: { path: { company_id: companyId } },
  });
  if (!data) notFound();
  return data;
}
