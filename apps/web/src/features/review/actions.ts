"use server";

import { revalidatePath } from "next/cache";

import { reviewCopy } from "@/content/es";
import { failure, type ActionResult } from "@/lib/actions";
import { serverApi } from "@/lib/api/server";

import { editSchema } from "./schemas";

function refresh(evaluationId: string, findingId?: string): void {
  revalidatePath(`/app/revision/${evaluationId}`);
  if (findingId) revalidatePath(`/app/revision/${evaluationId}/hallazgos/${findingId}`);
}

export async function approveFindingAction(
  evaluationId: string,
  findingId: string,
  comment: string,
): Promise<ActionResult> {
  const api = await serverApi();
  const { error } = await api.POST("/api/v1/findings/{finding_id}/approve", {
    params: { path: { finding_id: findingId } },
    body: { comment: comment.trim() || null },
  });
  if (error) return failure(error);
  refresh(evaluationId, findingId);
  return { ok: true, message: reviewCopy.actions.saved };
}

export async function discardFindingAction(
  evaluationId: string,
  findingId: string,
  comment: string,
): Promise<ActionResult> {
  if (comment.trim().length < 10) return { ok: false, message: reviewCopy.actions.discardHint };
  const api = await serverApi();
  const { error } = await api.POST("/api/v1/findings/{finding_id}/discard", {
    params: { path: { finding_id: findingId } },
    body: { comment: comment.trim() },
  });
  if (error) return failure(error);
  refresh(evaluationId, findingId);
  return { ok: true, message: reviewCopy.actions.saved };
}

export async function editFindingAction(
  evaluationId: string,
  findingId: string,
  input: unknown,
): Promise<ActionResult> {
  const parsed = editSchema.safeParse(input);
  if (!parsed.success) return { ok: false, message: reviewCopy.modelError };
  const api = await serverApi();
  const { error } = await api.PATCH("/api/v1/findings/{finding_id}", {
    params: { path: { finding_id: findingId } },
    body: { ...parsed.data, comment: parsed.data.comment || null },
  });
  if (error) return failure(error);
  refresh(evaluationId, findingId);
  return { ok: true, message: reviewCopy.actions.saved };
}

export async function approveEvaluationAction(evaluationId: string): Promise<ActionResult> {
  const api = await serverApi();
  const { error } = await api.POST("/api/v1/evaluations/{evaluation_id}/approve", {
    params: { path: { evaluation_id: evaluationId } },
  });
  if (error) return failure(error);
  refresh(evaluationId);
  return { ok: true, message: reviewCopy.decision.approved };
}

export async function rejectEvaluationAction(
  evaluationId: string,
  reason: string,
): Promise<ActionResult> {
  const api = await serverApi();
  const { error } = await api.POST("/api/v1/evaluations/{evaluation_id}/reject", {
    params: { path: { evaluation_id: evaluationId } },
    body: { reason: reason.trim() },
  });
  if (error) return failure(error);
  refresh(evaluationId);
  return { ok: true, message: reviewCopy.decision.rejected };
}
