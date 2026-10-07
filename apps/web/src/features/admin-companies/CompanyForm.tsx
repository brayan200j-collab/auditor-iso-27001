"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState, useTransition } from "react";
import { useForm } from "react-hook-form";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { describedBy, Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { adminCompanies } from "@/content/es";
import type { ActionResult } from "@/lib/actions";

import { createCompanyAction, updateCompanyAction } from "./actions";
import { companySchema, type CompanyFormInput, type CompanyFormValues } from "./schemas";

type CompanyFormProps = {
  companyId?: string;
  defaults?: Partial<CompanyFormInput>;
};

const EMPTY: CompanyFormInput = { name: "", taxId: "", sector: "", city: "", active: true };

export function CompanyForm({ companyId, defaults }: CompanyFormProps) {
  const [result, setResult] = useState<ActionResult | null>(null);
  const [pending, startTransition] = useTransition();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CompanyFormInput, unknown, CompanyFormValues>({
    resolver: zodResolver(companySchema),
    defaultValues: { ...EMPTY, ...defaults },
  });

  const onSubmit = handleSubmit((values) => {
    startTransition(async () => {
      const outcome = companyId
        ? await updateCompanyAction(companyId, values)
        : await createCompanyAction(values);
      setResult(outcome);
      if (outcome.ok && !companyId) reset(EMPTY);
    });
  });

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
      {result ? <Alert tone={result.ok ? "success" : "danger"}>{result.message}</Alert> : null}
      <div className="grid gap-4 md:grid-cols-2">
        <Field id="company-name" label={adminCompanies.name} error={errors.name?.message}>
          <Input
            id="company-name"
            aria-invalid={Boolean(errors.name)}
            aria-describedby={describedBy("company-name", errors.name?.message)}
            {...register("name")}
          />
        </Field>
        <Field
          id="company-tax-id"
          label={adminCompanies.taxId}
          hint={adminCompanies.taxIdHint}
          error={errors.taxId?.message}
        >
          <Input
            id="company-tax-id"
            inputMode="numeric"
            aria-invalid={Boolean(errors.taxId)}
            aria-describedby={describedBy(
              "company-tax-id",
              errors.taxId?.message,
              adminCompanies.taxIdHint,
            )}
            {...register("taxId")}
          />
        </Field>
        <Field id="company-sector" label={adminCompanies.sector}>
          <Input id="company-sector" {...register("sector")} />
        </Field>
        <Field id="company-city" label={adminCompanies.city}>
          <Input id="company-city" {...register("city")} />
        </Field>
      </div>
      {companyId ? (
        <label className="text-foreground flex items-center gap-2 text-sm">
          <input type="checkbox" className="size-4" {...register("active")} />
          {adminCompanies.active}
        </label>
      ) : null}
      <div>
        <Button type="submit" disabled={pending}>
          {pending
            ? adminCompanies.saving
            : companyId
              ? adminCompanies.save
              : adminCompanies.create}
        </Button>
      </div>
    </form>
  );
}
