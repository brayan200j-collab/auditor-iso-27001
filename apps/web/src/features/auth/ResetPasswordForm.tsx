"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useState, useTransition } from "react";
import { useForm } from "react-hook-form";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { describedBy, Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { auth } from "@/content/es";

import { resetPasswordAction, type ActionResult } from "./actions";
import { resetSchema, type ResetInput } from "./schemas";

export function ResetPasswordForm() {
  const [result, setResult] = useState<ActionResult | null>(null);
  const [pending, startTransition] = useTransition();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetInput>({ resolver: zodResolver(resetSchema) });

  const onSubmit = handleSubmit((values) => {
    startTransition(async () => setResult(await resetPasswordAction(values)));
  });

  if (result?.ok) {
    return (
      <div className="flex flex-col gap-4">
        <Alert tone="success">{result.message}</Alert>
        <Link href="/login" className="text-primary text-sm underline-offset-4 hover:underline">
          {auth.recovery.backToLogin}
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
      {result && !result.ok ? <Alert tone="danger">{result.message}</Alert> : null}
      <Field
        id="password"
        label={auth.reset.password}
        hint={auth.reset.rule}
        error={errors.password?.message}
      >
        <Input
          id="password"
          type="password"
          autoComplete="new-password"
          aria-invalid={Boolean(errors.password)}
          aria-describedby={describedBy("password", errors.password?.message, auth.reset.rule)}
          {...register("password")}
        />
      </Field>
      <Field id="confirm" label={auth.reset.confirm} error={errors.confirm?.message}>
        <Input
          id="confirm"
          type="password"
          autoComplete="new-password"
          aria-invalid={Boolean(errors.confirm)}
          aria-describedby={describedBy("confirm", errors.confirm?.message)}
          {...register("confirm")}
        />
      </Field>
      <Button type="submit" disabled={pending}>
        {pending ? auth.reset.submitting : auth.reset.submit}
      </Button>
    </form>
  );
}
