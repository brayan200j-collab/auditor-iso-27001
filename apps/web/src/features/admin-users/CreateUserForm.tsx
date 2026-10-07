"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState, useTransition } from "react";
import { useForm, useWatch } from "react-hook-form";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { describedBy, Field } from "@/components/ui/field";
import { Input, Select } from "@/components/ui/input";
import { adminUsers, roleLabels } from "@/content/es";
import type { ActionResult } from "@/lib/actions";

import { createUserAction } from "./actions";
import { createUserSchema, ROLES, type CreateUserValues } from "./schemas";

type CompanyOption = { id: string; name: string };

const EMPTY: CreateUserValues = { email: "", fullName: "", role: "SME", companyId: "" };

export function CreateUserForm({ companies }: { companies: CompanyOption[] }) {
  const [result, setResult] = useState<ActionResult | null>(null);
  const [pending, startTransition] = useTransition();
  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm<CreateUserValues>({ resolver: zodResolver(createUserSchema), defaultValues: EMPTY });
  const role = useWatch({ control, name: "role" });

  const onSubmit = handleSubmit((values) => {
    startTransition(async () => {
      const outcome = await createUserAction(values);
      setResult(outcome);
      if (outcome.ok) reset(EMPTY);
    });
  });

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
      <p className="text-muted-foreground text-sm">{adminUsers.inviteHint}</p>
      {result ? <Alert tone={result.ok ? "success" : "danger"}>{result.message}</Alert> : null}
      <div className="grid gap-4 md:grid-cols-2">
        <Field id="user-email" label={adminUsers.email} error={errors.email?.message}>
          <Input
            id="user-email"
            type="email"
            autoComplete="off"
            aria-invalid={Boolean(errors.email)}
            aria-describedby={describedBy("user-email", errors.email?.message)}
            {...register("email")}
          />
        </Field>
        <Field id="user-name" label={adminUsers.fullName} error={errors.fullName?.message}>
          <Input
            id="user-name"
            aria-invalid={Boolean(errors.fullName)}
            aria-describedby={describedBy("user-name", errors.fullName?.message)}
            {...register("fullName")}
          />
        </Field>
        <Field id="user-role" label={adminUsers.role}>
          <Select id="user-role" {...register("role")}>
            {ROLES.map((value) => (
              <option key={value} value={value}>
                {roleLabels[value]}
              </option>
            ))}
          </Select>
        </Field>
        {role === "SME" ? (
          <Field
            id="user-company"
            label={adminUsers.company}
            hint={adminUsers.companyHint}
            error={errors.companyId?.message}
          >
            <Select
              id="user-company"
              aria-invalid={Boolean(errors.companyId)}
              aria-describedby={describedBy(
                "user-company",
                errors.companyId?.message,
                adminUsers.companyHint,
              )}
              {...register("companyId")}
            >
              <option value="">{adminUsers.companyPlaceholder}</option>
              {companies.map((company) => (
                <option key={company.id} value={company.id}>
                  {company.name}
                </option>
              ))}
            </Select>
          </Field>
        ) : null}
      </div>
      <div>
        <Button type="submit" disabled={pending}>
          {pending ? adminUsers.creating : adminUsers.create}
        </Button>
      </div>
    </form>
  );
}
