"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useEffect, useState, useTransition } from "react";
import { useForm } from "react-hook-form";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { describedBy, Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { auth } from "@/content/es";

import { signInAction } from "./actions";
import { loginSchema, type LoginInput } from "./schemas";

const SLOW_AFTER_MS = 5_000;

export function LoginForm() {
  const [serverError, setServerError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const [slow, setSlow] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginInput>({ resolver: zodResolver(loginSchema) });

  // After a few seconds, explain the wait: a sleeping server can take up to a minute to start.
  useEffect(() => {
    if (!pending) return;
    const timer = setTimeout(() => setSlow(true), SLOW_AFTER_MS);
    return () => clearTimeout(timer);
  }, [pending]);

  const onSubmit = handleSubmit((values) => {
    setServerError(null);
    setSlow(false);
    startTransition(async () => {
      const result = await signInAction(values);
      if (result && !result.ok) setServerError(result.message);
    });
  });

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
      {serverError ? <Alert tone="danger">{serverError}</Alert> : null}
      <Field id="email" label={auth.login.email} error={errors.email?.message}>
        <Input
          id="email"
          type="email"
          autoComplete="email"
          aria-invalid={Boolean(errors.email)}
          aria-describedby={describedBy("email", errors.email?.message)}
          {...register("email")}
        />
      </Field>
      <Field id="password" label={auth.login.password} error={errors.password?.message}>
        <Input
          id="password"
          type="password"
          autoComplete="current-password"
          aria-invalid={Boolean(errors.password)}
          aria-describedby={describedBy("password", errors.password?.message)}
          {...register("password")}
        />
      </Field>
      <Button type="submit" disabled={pending}>
        {pending ? auth.login.submitting : auth.login.submit}
      </Button>
      <p role="status" aria-live="polite" className="text-muted-foreground text-sm">
        {pending && slow ? auth.login.slow : ""}
      </p>
      <Link href="/recuperar" className="text-primary text-sm underline-offset-4 hover:underline">
        {auth.login.forgot}
      </Link>
    </form>
  );
}
