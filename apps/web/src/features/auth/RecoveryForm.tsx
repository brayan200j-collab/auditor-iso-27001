"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState, useTransition } from "react";
import { useForm } from "react-hook-form";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { describedBy, Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { auth } from "@/content/es";

import { requestRecoveryAction } from "./actions";
import { recoverySchema, type RecoveryInput } from "./schemas";

export function RecoveryForm() {
  const [message, setMessage] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RecoveryInput>({ resolver: zodResolver(recoverySchema) });

  const onSubmit = handleSubmit((values) => {
    startTransition(async () => {
      const result = await requestRecoveryAction(values);
      setMessage(result.message ?? auth.recovery.sent);
    });
  });

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
      {message ? <Alert tone="info">{message}</Alert> : null}
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
      <Button type="submit" disabled={pending}>
        {pending ? auth.recovery.submitting : auth.recovery.submit}
      </Button>
    </form>
  );
}
