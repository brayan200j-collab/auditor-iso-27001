import "server-only";

import { notFound } from "next/navigation";

import type { components } from "@/lib/api/schema";
import { serverApi } from "@/lib/api/server";

export type Review = components["schemas"]["ReviewResponse"];
export type ReviewItem = components["schemas"]["ReviewItemResponse"];
export type FindingDetail = components["schemas"]["FindingDetailResponse"];

export async function getReview(evaluationId: string): Promise<Review | null> {
  const api = await serverApi();
  const { data, response } = await api.GET("/api/v1/reviews/{evaluation_id}", {
    params: { path: { evaluation_id: evaluationId } },
  });
  if (response.status === 404) notFound();
  return data ?? null;
}

export async function getFinding(findingId: string): Promise<FindingDetail> {
  const api = await serverApi();
  const { data } = await api.GET("/api/v1/findings/{finding_id}", {
    params: { path: { finding_id: findingId } },
  });
  if (!data) notFound();
  return data;
}
