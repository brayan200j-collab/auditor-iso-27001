"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { useForm, type UseFormRegisterReturn } from "react-hook-form";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { describedBy, Field } from "@/components/ui/field";
import { Input, Textarea } from "@/components/ui/input";
import { surveyCopy as copy } from "@/content/es";
import type { ActionResult } from "@/lib/actions";

import { submitSurveyAction } from "./actions";
import { surveySchema, type SurveyInput, type SurveyValues } from "./schemas";

type Option = { value: string; label: string };

const SCALE: Option[] = ["1", "2", "3", "4", "5"].map((value) => ({ value, label: value }));
const YES_NO: Option[] = [
  { value: "yes", label: copy.yes },
  { value: "no", label: copy.no },
];
const PAY: Option[] = (["YES", "MAYBE", "NO"] as const).map((value) => ({
  value,
  label: copy.pay[value],
}));

function Choice({
  name,
  legend,
  options,
  hint,
  error,
  field,
}: {
  name: string;
  legend: string;
  options: Option[];
  hint?: string;
  error?: string;
  field: UseFormRegisterReturn;
}) {
  return (
    <fieldset className="flex flex-col gap-2" aria-describedby={describedBy(name, error, hint)}>
      <legend className="text-foreground mb-1 text-sm font-medium">{legend}</legend>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <label
            key={option.value}
            className="border-border has-[:checked]:border-primary has-[:checked]:bg-primary/10 flex min-w-12 cursor-pointer items-center justify-center gap-2 rounded-md border px-3 py-2 text-sm has-[:focus-visible]:ring-2"
          >
            <input type="radio" value={option.value} className="sr-only" {...field} />
            {option.label}
          </label>
        ))}
      </div>
      {hint && !error ? (
        <p id={`${name}-hint`} className="text-muted-foreground text-xs">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={`${name}-error`} role="alert" className="text-danger text-xs font-medium">
          {error}
        </p>
      ) : null}
    </fieldset>
  );
}

export function SurveyForm({ evaluationId }: { evaluationId: string }) {
  const router = useRouter();
  const [result, setResult] = useState<ActionResult | null>(null);
  const [pending, startTransition] = useTransition();
  const {
    register,
    handleSubmit,
    getValues,
    formState: { errors },
  } = useForm<SurveyInput, unknown, SurveyValues>({
    resolver: zodResolver(surveySchema),
    defaultValues: { comments: "", manual_time_hours: "", system_time_hours: "" },
  });

  const onSubmit = handleSubmit(
    () => {
      // The server action validates the raw answers again with the same schema.
      const raw = getValues();
      startTransition(async () => {
        const outcome = await submitSurveyAction(evaluationId, raw);
        setResult(outcome);
        if (outcome.ok) router.push(`/app/evaluaciones/${evaluationId}/resultados`);
      });
    },
    () => setResult({ ok: false, message: copy.invalid }),
  );

  const scale = (
    name: "usefulness" | "ease_of_use" | "trust_in_results" | "willingness_to_use",
  ) => (
    <Choice
      name={name}
      legend={copy.questions[name]}
      options={SCALE}
      hint={copy.scaleHint}
      error={errors[name]?.message}
      field={register(name)}
    />
  );

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-6">
      {result ? <Alert tone={result.ok ? "success" : "danger"}>{result.message}</Alert> : null}
      {scale("usefulness")}
      {scale("ease_of_use")}
      {scale("trust_in_results")}
      <Choice
        name="actionable_recommendations"
        legend={copy.questions.actionable_recommendations}
        options={YES_NO}
        error={errors.actionable_recommendations?.message}
        field={register("actionable_recommendations")}
      />
      <div className="grid gap-4 md:grid-cols-2">
        {(["manual_time_hours", "system_time_hours"] as const).map((name) => (
          <Field
            key={name}
            id={name}
            label={copy.questions[name]}
            hint={copy.hoursHint}
            error={errors[name]?.message}
          >
            <Input
              id={name}
              inputMode="decimal"
              aria-invalid={Boolean(errors[name])}
              aria-describedby={describedBy(name, errors[name]?.message, copy.hoursHint)}
              {...register(name)}
            />
          </Field>
        ))}
      </div>
      {scale("willingness_to_use")}
      <Choice
        name="willingness_to_pay"
        legend={copy.questions.willingness_to_pay}
        options={PAY}
        error={errors.willingness_to_pay?.message}
        field={register("willingness_to_pay")}
      />
      <Field id="comments" label={copy.questions.comments}>
        <Textarea id="comments" maxLength={2000} {...register("comments")} />
      </Field>
      <div>
        <Button type="submit" disabled={pending}>
          {copy.submit}
        </Button>
      </div>
    </form>
  );
}
