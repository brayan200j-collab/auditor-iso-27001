"use client";

import { useState, useTransition } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { checklistCopy } from "@/content/es";
import type { ActionResult } from "@/lib/actions";

import { createDraftAction, publishVersionAction } from "./actions";

function useAction() {
  const [result, setResult] = useState<ActionResult | null>(null);
  const [pending, startTransition] = useTransition();
  const run = (action: () => Promise<ActionResult>) =>
    startTransition(async () => setResult((await action()) ?? null));
  return { result, pending, run };
}

export function CreateDraftButton() {
  const { result, pending, run } = useAction();
  return (
    <div className="flex flex-col gap-2">
      {result && !result.ok ? <Alert tone="danger">{result.message}</Alert> : null}
      <div>
        <Button type="button" disabled={pending} onClick={() => run(createDraftAction)}>
          {checklistCopy.createDraft}
        </Button>
      </div>
    </div>
  );
}

export function PublishButton({ versionId }: { versionId: string }) {
  const { result, pending, run } = useAction();
  return (
    <div className="flex flex-col gap-2">
      <p className="text-muted-foreground text-sm">{checklistCopy.publishHint}</p>
      {result ? <Alert tone={result.ok ? "success" : "danger"}>{result.message}</Alert> : null}
      <div>
        <Button
          type="button"
          disabled={pending}
          onClick={() => run(() => publishVersionAction(versionId))}
        >
          {checklistCopy.publish}
        </Button>
      </div>
    </div>
  );
}
