"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState, useTransition } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { describedBy, Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { evaluations } from "@/content/es";

import { createEvaluationAction } from "./actions";

const schema = z.object({
  title: z.string().trim().min(3, evaluations.titleError).max(200, evaluations.titleError),
});
type Values = z.infer<typeof schema>;

export function CreateEvaluationForm() {
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { title: "" } });

  const onSubmit = handleSubmit((values) => {
    setError(null);
    startTransition(async () => {
      const result = await createEvaluationAction(values);
      if (result && !result.ok) setError(result.message);
    });
  });

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
      {error ? <Alert tone="danger">{error}</Alert> : null}
      <Field
        id="evaluation-title"
        label={evaluations.titleLabel}
        hint={evaluations.newDescription}
        error={errors.title?.message}
      >
        <Input
          id="evaluation-title"
          aria-invalid={Boolean(errors.title)}
          aria-describedby={describedBy(
            "evaluation-title",
            errors.title?.message,
            evaluations.newDescription,
          )}
          {...register("title")}
        />
      </Field>
      <div>
        <Button type="submit" disabled={pending}>
          {pending ? evaluations.creating : evaluations.create}
        </Button>
      </div>
    </form>
  );
}
