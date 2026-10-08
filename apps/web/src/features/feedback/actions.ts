"use server";

import { revalidatePath } from "next/cache";

import { surveyCopy } from "@/content/es";
import { failure, type ActionResult } from "@/lib/actions";
import { serverApi } from "@/lib/api/server";

import { surveySchema, type SurveyInput } from "./schemas";

export async function submitSurveyAction(
  evaluationId: string,
  input: SurveyInput,
): Promise<ActionResult> {
  const parsed = surveySchema.safeParse(input);
  if (!parsed.success) return { ok: false, message: surveyCopy.invalid };
  const values = parsed.data;
  const api = await serverApi();
  const { error } = await api.POST("/api/v1/feedback", {
    body: {
      evaluation_id: evaluationId,
      usefulness: Number(values.usefulness),
      ease_of_use: Number(values.ease_of_use),
      trust_in_results: Number(values.trust_in_results),
      actionable_recommendations: values.actionable_recommendations === "yes",
      manual_time_hours: values.manual_time_hours,
      system_time_hours: values.system_time_hours,
      willingness_to_use: Number(values.willingness_to_use),
      willingness_to_pay: values.willingness_to_pay,
      comments: values.comments || null,
    },
  });
  if (error) return failure(error);
  revalidatePath(`/app/evaluaciones/${evaluationId}/resultados`);
  return { ok: true, message: surveyCopy.sent };
}
