"use client";

import { useState, useTransition } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { consentCopy } from "@/content/es";
import type { ActionResult } from "@/lib/actions";

import { giveConsentAction } from "./actions";

type ConsentFormProps = { evaluationId: string; version: string; text: string };

export function ConsentForm({ evaluationId, version, text }: ConsentFormProps) {
  const [accepted, setAccepted] = useState(false);
  const [result, setResult] = useState<ActionResult | null>(null);
  const [pending, startTransition] = useTransition();

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!accepted) {
      setResult({ ok: false, message: consentCopy.required });
      return;
    }
    startTransition(async () => setResult(await giveConsentAction(evaluationId, version)));
  };

  return (
    <form onSubmit={submit} className="flex flex-col gap-4">
      <div className="border-border bg-surface-muted flex max-h-80 flex-col gap-3 overflow-y-auto rounded-md border p-4 text-sm">
        {text.split("\n").map((paragraph) => (
          <p key={paragraph} className="text-foreground leading-relaxed">
            {paragraph}
          </p>
        ))}
        <p className="text-muted-foreground text-xs">{consentCopy.version(version)}</p>
      </div>
      {result ? <Alert tone={result.ok ? "success" : "danger"}>{result.message}</Alert> : null}
      <label className="text-foreground flex items-start gap-2 text-sm">
        <input
          type="checkbox"
          className="mt-0.5 size-4"
          checked={accepted}
          onChange={(event) => setAccepted(event.target.checked)}
        />
        {consentCopy.checkbox}
      </label>
      <div>
        <Button type="submit" disabled={pending}>
          {pending ? consentCopy.submitting : consentCopy.submit}
        </Button>
      </div>
    </form>
  );
}
