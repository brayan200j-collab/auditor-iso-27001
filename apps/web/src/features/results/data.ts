import "server-only";

import { notFound } from "next/navigation";

import type { components } from "@/lib/api/schema";
import { serverApi } from "@/lib/api/server";

export type Results = components["schemas"]["ResultsResponse"];
export type ResultFinding = components["schemas"]["ResultFindingResponse"];

/** Approved results; null while the human review has not finished. */
export async function getResults(evaluationId: string): Promise<Results | null> {
  const api = await serverApi();
  const { data, response } = await api.GET("/api/v1/evaluations/{evaluation_id}/findings", {
    params: { path: { evaluation_id: evaluationId } },
  });
  if (response.status === 404) notFound();
  return data ?? null;
}
