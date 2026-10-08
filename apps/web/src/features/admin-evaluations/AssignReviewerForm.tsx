"use client";

import { useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/input";
import { evaluations } from "@/content/es";

import { assignReviewerAction } from "./actions";

type AssignReviewerFormProps = {
  evaluationId: string;
  evaluationTitle: string;
  currentReviewerId: string | null;
  reviewers: { id: string; name: string }[];
  disabled?: boolean;
};

export function AssignReviewerForm({
  evaluationId,
  evaluationTitle,
  currentReviewerId,
  reviewers,
  disabled = false,
}: AssignReviewerFormProps) {
  const [reviewerId, setReviewerId] = useState(currentReviewerId ?? "");
  const [message, setMessage] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const selectId = `reviewer-${evaluationId}`;

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!reviewerId) return;
    startTransition(async () => {
      const result = await assignReviewerAction(evaluationId, reviewerId);
      setMessage(result.message ?? null);
    });
  };

  return (
    <form onSubmit={submit} className="flex flex-wrap items-center gap-2">
      <label htmlFor={selectId} className="sr-only">
        {evaluations.assignLabel(evaluationTitle)}
      </label>
      <Select
        id={selectId}
        value={reviewerId}
        disabled={disabled || pending}
        onChange={(event) => setReviewerId(event.target.value)}
        className="h-8 w-48"
      >
        <option value="">{evaluations.unassigned}</option>
        {reviewers.map((reviewer) => (
          <option key={reviewer.id} value={reviewer.id}>
            {reviewer.name}
          </option>
        ))}
      </Select>
      <Button
        type="submit"
        size="sm"
        variant="outline"
        disabled={disabled || pending || !reviewerId || reviewerId === currentReviewerId}
      >
        {evaluations.assign}
      </Button>
      <span role="status" className="text-muted-foreground text-xs">
        {message}
      </span>
    </form>
  );
}
