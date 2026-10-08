"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { processingCopy } from "@/content/es";
import { browserApi } from "@/lib/api/browser";
import { apiErrorMessage } from "@/lib/api/errors";

type Kind = "start" | "retry";

const LABELS: Record<Kind, { idle: string; busy: string; hint: string }> = {
  start: {
    idle: processingCopy.start,
    busy: processingCopy.starting,
    hint: processingCopy.startHint,
  },
  retry: {
    idle: processingCopy.retry,
    busy: processingCopy.retrying,
    hint: processingCopy.retryHint,
  },
};

export function ProcessingAction({ evaluationId, kind }: { evaluationId: string; kind: Kind }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const labels = LABELS[kind];

  const run = () => {
    setError(null);
    startTransition(async () => {
      const path =
        kind === "start"
          ? "/api/v1/evaluations/{evaluation_id}/start"
          : "/api/v1/evaluations/{evaluation_id}/retry";
      const { error: failure } = await browserApi.POST(path, {
        params: { path: { evaluation_id: evaluationId } },
      });
      if (failure) {
        setError(apiErrorMessage(failure));
        return;
      }
      router.refresh();
    });
  };

  return (
    <div className="flex flex-col gap-2">
      <p className="text-muted-foreground text-sm">{labels.hint}</p>
      {error ? <Alert tone="danger">{error}</Alert> : null}
      <div>
        <Button type="button" onClick={run} disabled={pending}>
          {pending ? labels.busy : labels.idle}
        </Button>
      </div>
    </div>
  );
}
