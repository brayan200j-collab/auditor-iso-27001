import { z } from "zod";

import { adminCompanies } from "@/content/es";

const TAX_ID = /^\d{5,15}(-\d)?$/;

/** Removes the dots and spaces people usually type in a NIT (900.123.456-7 → 900123456-7). */
export function normalizeTaxId(value: string): string {
  return value.replace(/[.\s]/g, "");
}

export const companySchema = z.object({
  name: z
    .string()
    .trim()
    .min(2, adminCompanies.validation.name)
    .max(200, adminCompanies.validation.name),
  taxId: z
    .string()
    .trim()
    .transform(normalizeTaxId)
    .refine((value) => value === "" || TAX_ID.test(value), adminCompanies.validation.taxId),
  sector: z.string().trim().max(120),
  city: z.string().trim().max(120),
  active: z.boolean(),
});

export type CompanyFormInput = z.input<typeof companySchema>;
export type CompanyFormValues = z.output<typeof companySchema>;
