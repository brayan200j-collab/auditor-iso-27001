import "server-only";

import type { components } from "@/lib/api/schema";
import { serverApi } from "@/lib/api/server";

export type SurveyStatus = components["schemas"]["SurveyStatusResponse"];

export async function getSurveyStatus(evaluationId: string): Promise<SurveyStatus | null> {
  const api = await serverApi();
  const { data } = await api.GET("/api/v1/evaluations/{evaluation_id}/feedback", {
    params: { path: { evaluation_id: evaluationId } },
  });
  return data ?? null;
}
