"use server";

import { revalidatePath } from "next/cache";

import { evaluations } from "@/content/es";
import { failure, type ActionResult } from "@/lib/actions";
import { serverApi } from "@/lib/api/server";

export async function assignReviewerAction(
  evaluationId: string,
  reviewerId: string,
): Promise<ActionResult> {
  const api = await serverApi();
  const { error } = await api.PUT("/api/v1/evaluations/{evaluation_id}/reviewer", {
    params: { path: { evaluation_id: evaluationId } },
    body: { reviewer_id: reviewerId },
  });
  if (error) return failure(error);
  revalidatePath("/app/admin/evaluaciones");
  return { ok: true, message: evaluations.assigned };
}
