"use client";

import { useState, useTransition } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Textarea } from "@/components/ui/input";
import { reviewCopy } from "@/content/es";
import type { ActionResult } from "@/lib/actions";

import { approveEvaluationAction, rejectEvaluationAction } from "./actions";

const d = reviewCopy.decision;

export function DecisionPanel({
  evaluationId,
  pending,
}: {
  evaluationId: string;
  pending: number;
}) {
  const [reason, setReason] = useState("");
  const [result, setResult] = useState<ActionResult | null>(null);
  const [busy, startTransition] = useTransition();

  return (
    <Card className="flex flex-col gap-4">
      <CardTitle>{d.title}</CardTitle>
      {result ? <Alert tone={result.ok ? "success" : "danger"}>{result.message}</Alert> : null}
      <div className="flex flex-col gap-2">
        <p className="text-muted-foreground text-sm">{d.approveHint}</p>
        {pending > 0 ? <Alert tone="warning">{d.pending(pending)}</Alert> : null}
        <div>
          <Button
            type="button"
            disabled={busy || pending > 0}
            onClick={() =>
              startTransition(async () => setResult(await approveEvaluationAction(evaluationId)))
            }
          >
            {d.approve}
          </Button>
        </div>
      </div>
      <div className="border-border flex flex-col gap-2 border-t pt-4">
        <p className="text-muted-foreground text-sm">{d.rejectHint}</p>
        <Field id="reject-reason" label={d.reason}>
          <Textarea id="reject-reason" value={reason} onChange={(e) => setReason(e.target.value)} />
        </Field>
        <div>
          <Button
            type="button"
            variant="danger"
            disabled={busy || reason.trim().length < 10}
            onClick={() =>
              startTransition(async () =>
                setResult(await rejectEvaluationAction(evaluationId, reason)),
              )
            }
          >
            {d.reject}
          </Button>
        </div>
      </div>
    </Card>
  );
}
