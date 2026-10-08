import "server-only";

import { notFound } from "next/navigation";

import type { EvaluationStatus } from "@/content/es";
import type { components } from "@/lib/api/schema";
import { serverApi } from "@/lib/api/server";

export type Evaluation = components["schemas"]["EvaluationResponse"];
export type EvaluationPage = components["schemas"]["EvaluationPage"];
export type EvaluationDetail = components["schemas"]["EvaluationDetailResponse"];
export type ConsentText = components["schemas"]["ConsentTextResponse"];

export async function listEvaluations(
  page: number,
  status?: EvaluationStatus,
): Promise<EvaluationPage> {
  const api = await serverApi();
  const { data, error } = await api.GET("/api/v1/evaluations", {
    params: { query: { page, page_size: 20, ...(status ? { status } : {}) } },
  });
  if (!data) throw new Error(`Unable to list evaluations: ${JSON.stringify(error)}`);
  return data;
}

export async function getEvaluation(evaluationId: string): Promise<EvaluationDetail> {
  const api = await serverApi();
  const { data } = await api.GET("/api/v1/evaluations/{evaluation_id}", {
    params: { path: { evaluation_id: evaluationId } },
  });
  if (!data) notFound();
  return data;
}

export async function getConsentText(): Promise<ConsentText> {
  const api = await serverApi();
  const { data, error } = await api.GET("/api/v1/consent");
  if (!data) throw new Error(`Unable to load consent: ${JSON.stringify(error)}`);
  return data;
}
