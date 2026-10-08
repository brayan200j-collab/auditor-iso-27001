"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { z } from "zod";

import { consentCopy, evaluations } from "@/content/es";
import { failure, type ActionResult } from "@/lib/actions";
import { serverApi } from "@/lib/api/server";

const createSchema = z.object({ title: z.string().trim().min(3).max(200) });

export async function createEvaluationAction(input: unknown): Promise<ActionResult> {
  const parsed = createSchema.safeParse(input);
  if (!parsed.success) return { ok: false, message: evaluations.titleError };
  const api = await serverApi();
  const { data, error } = await api.POST("/api/v1/evaluations", { body: parsed.data });
  if (!data) return failure(error);
  revalidatePath("/app/evaluaciones");
  redirect(`/app/evaluaciones/${data.id}`);
}

export async function giveConsentAction(
  evaluationId: string,
  version: string,
): Promise<ActionResult> {
  const api = await serverApi();
  const { error } = await api.POST("/api/v1/evaluations/{evaluation_id}/consent", {
    params: { path: { evaluation_id: evaluationId } },
    body: { version },
  });
  if (error) return failure(error);
  revalidatePath(`/app/evaluaciones/${evaluationId}`);
  return { ok: true, message: consentCopy.accepted };
}
