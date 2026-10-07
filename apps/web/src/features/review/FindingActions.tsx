"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { useForm } from "react-hook-form";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Select, Textarea } from "@/components/ui/input";
import {
  effortLabels,
  findingStatusLabels,
  priorityLabels,
  reviewCopy,
  riskLabels,
} from "@/content/es";
import type { ActionResult } from "@/lib/actions";

import { approveFindingAction, discardFindingAction, editFindingAction } from "./actions";
import { editSchema, type EditValues } from "./schemas";

type Mode = "approve" | "edit" | "discard";

type FindingActionsProps = {
  evaluationId: string;
  findingId: string;
  canApprove: boolean;
  defaults: EditValues;
};

const a = reviewCopy.actions;

export function FindingActions({
  evaluationId,
  findingId,
  canApprove,
  defaults,
}: FindingActionsProps) {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>(canApprove ? "approve" : "edit");
  const [comment, setComment] = useState("");
  const [result, setResult] = useState<ActionResult | null>(null);
  const [pending, startTransition] = useTransition();
  const { register, handleSubmit } = useForm<EditValues>({
    resolver: zodResolver(editSchema),
    defaultValues: defaults,
  });

  const done = (outcome: ActionResult) => {
    setResult(outcome);
    if (outcome.ok) router.push(`/app/revision/${evaluationId}`);
  };

  const submitEdit = handleSubmit(
    (values) =>
      startTransition(async () => done(await editFindingAction(evaluationId, findingId, values))),
    () => setResult({ ok: false, message: reviewCopy.modelError }),
  );

  return (
    <div className="flex flex-col gap-4">
      <div role="group" aria-label={a.choose} className="flex flex-wrap gap-2">
        {(["approve", "edit", "discard"] as const).map((option) => (
          <Button
            key={option}
            type="button"
            aria-pressed={mode === option}
            variant={mode === option ? "primary" : "outline"}
            size="sm"
            disabled={option === "approve" && !canApprove}
            onClick={() => setMode(option)}
          >
            {option === "approve" ? a.approve : option === "edit" ? a.edit : a.discard}
          </Button>
        ))}
      </div>
      {result ? <Alert tone={result.ok ? "success" : "danger"}>{result.message}</Alert> : null}

      {mode === "approve" ? (
        <div className="flex flex-col gap-3">
          <p className="text-muted-foreground text-sm">{a.approveHint}</p>
          <Field id="approve-comment" label={a.comment}>
            <Textarea
              id="approve-comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
          </Field>
          <div>
            <Button
              type="button"
              disabled={pending}
              onClick={() =>
                startTransition(async () =>
                  done(await approveFindingAction(evaluationId, findingId, comment)),
                )
              }
            >
              {a.approve}
            </Button>
          </div>
        </div>
      ) : null}

      {mode === "edit" ? (
        <form onSubmit={submitEdit} noValidate className="flex flex-col gap-3">
          <Field id="edit-status" label={a.status}>
            <Select id="edit-status" {...register("status")}>
              {Object.entries(findingStatusLabels).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </Select>
          </Field>
          <Field id="edit-gap" label={reviewCopy.gap}>
            <Textarea id="edit-gap" {...register("gap")} />
          </Field>
          <Field id="edit-recommendation" label={reviewCopy.recommendation}>
            <Textarea id="edit-recommendation" {...register("recommendation")} />
          </Field>
          <div className="grid gap-3 md:grid-cols-3">
            <Field id="edit-priority" label={reviewCopy.priority}>
              <Select id="edit-priority" {...register("priority")}>
                {Object.entries(priorityLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </Select>
            </Field>
            <Field id="edit-risk" label={reviewCopy.risk}>
              <Select id="edit-risk" {...register("risk_level")}>
                {Object.entries(riskLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </Select>
            </Field>
            <Field id="edit-effort" label={reviewCopy.effort}>
              <Select id="edit-effort" {...register("effort")}>
                {Object.entries(effortLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </Select>
            </Field>
          </div>
          <Field id="edit-comment" label={a.comment}>
            <Textarea id="edit-comment" {...register("comment")} />
          </Field>
          <div>
            <Button type="submit" disabled={pending}>
              {a.edit}
            </Button>
          </div>
        </form>
      ) : null}

      {mode === "discard" ? (
        <div className="flex flex-col gap-3">
          <Field id="discard-reason" label={a.reason} hint={a.discardHint}>
            <Textarea
              id="discard-reason"
              aria-describedby="discard-reason-hint"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
          </Field>
          <div>
            <Button
              type="button"
              variant="danger"
              disabled={pending}
              onClick={() =>
                startTransition(async () =>
                  done(await discardFindingAction(evaluationId, findingId, comment)),
                )
              }
            >
              {a.discard}
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
