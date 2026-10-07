"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState, useTransition } from "react";
import { useForm } from "react-hook-form";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { describedBy, Field } from "@/components/ui/field";
import { Input, Select } from "@/components/ui/input";
import { adminUsers } from "@/content/es";
import type { ActionResult } from "@/lib/actions";

import { setUserActiveAction, updateUserAction } from "./actions";
import { updateUserSchema, type UpdateUserValues } from "./schemas";

type EditUserFormProps = {
  userId: string;
  isSme: boolean;
  active: boolean;
  defaults: UpdateUserValues;
  companies: { id: string; name: string }[];
};

export function EditUserForm({ userId, isSme, active, defaults, companies }: EditUserFormProps) {
  const [result, setResult] = useState<ActionResult | null>(null);
  const [pending, startTransition] = useTransition();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<UpdateUserValues>({
    resolver: zodResolver(updateUserSchema),
    defaultValues: defaults,
  });

  const onSubmit = handleSubmit((values) => {
    startTransition(async () => setResult(await updateUserAction(userId, values)));
  });

  const toggleActive = () => {
    startTransition(async () => setResult(await setUserActiveAction(userId, !active)));
  };

  return (
    <div className="flex flex-col gap-6">
      {result ? <Alert tone={result.ok ? "success" : "danger"}>{result.message}</Alert> : null}
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
        <Field id="edit-name" label={adminUsers.fullName} error={errors.fullName?.message}>
          <Input
            id="edit-name"
            aria-invalid={Boolean(errors.fullName)}
            aria-describedby={describedBy("edit-name", errors.fullName?.message)}
            {...register("fullName")}
          />
        </Field>
        {isSme ? (
          <Field id="edit-company" label={adminUsers.company}>
            <Select id="edit-company" {...register("companyId")}>
              {companies.map((company) => (
                <option key={company.id} value={company.id}>
                  {company.name}
                </option>
              ))}
            </Select>
          </Field>
        ) : null}
        <div>
          <Button type="submit" disabled={pending}>
            {adminUsers.save}
          </Button>
        </div>
      </form>
      <div>
        <Button
          type="button"
          variant={active ? "danger" : "secondary"}
          disabled={pending}
          onClick={toggleActive}
        >
          {active ? adminUsers.deactivate : adminUsers.activate}
        </Button>
      </div>
    </div>
  );
}
